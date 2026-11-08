"""Proposal engine: sends numbered beats to LLM to propose 3-5 candidates as beat-ID ranges.

Converts LLM beat-ID ranges into timestamped candidate objects.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.llm import complete_json
from src.parser import format_timestamp

logger = logging.getLogger("src.propose")


PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start_beat_id": {"type": "string"},
                    "end_beat_id": {"type": "string"},
                    "hook_beat_id": {"type": "string"},
                    "cliffhanger_beat_id": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "start_beat_id",
                    "end_beat_id",
                    "hook_beat_id",
                    "cliffhanger_beat_id",
                    "rationale",
                ],
            },
        }
    },
    "required": ["candidates"],
}


def build_beats_prompt(episode_data: Dict[str, Any]) -> str:
    """Format episode beats into a compact, clearly indexed script for candidate proposal."""
    ep_num = episode_data["episode"]
    logline = episode_data.get("logline", "")
    beats = episode_data["beats"]

    lines = [
        f"EPISODE {ep_num}: {logline}",
        "",
        "TASK: Propose 3 to 5 candidate PROMO CLIPS for social media (TikTok, Reels, YouTube Shorts).",
        "A winning promo clip:",
        "1. Duration must be approximately 20 to 60 seconds long.",
        "2. Opens on an irresistible HOOK in the first 3 seconds (slap, cruel insult, public humiliation, shocking reveal).",
        "3. Ends on a gripping CLIFFHANGER (unresolved tension right before a revelation, punch, or decision).",
        "4. Standalone coherence: Must make total sense to someone who has never seen the show before.",
        "",
        "RULES:",
        "- You must specify clips ONLY using beat IDs (e.g. start_beat_id: 'E01-B003', end_beat_id: 'E01-B015').",
        "- DO NOT invent timestamps. Our code computes timestamps from beat IDs.",
        "- Ensure hook_beat_id is at or immediately after start_beat_id (within first 3 seconds).",
        "- Ensure cliffhanger_beat_id is the final high-stakes beat at or just before end_beat_id.",
        "",
        "EPISODE BEATS:",
    ]

    for b in beats:
        timing = f"({format_timestamp(b['start'])} - {format_timestamp(b['end'])})"
        if b["kind"] == "dialogue":
            emo = f" ({b['emotion']})" if b.get("emotion") else ""
            lines.append(f"[{b['id']}] {timing} {b['speaker']}{emo}: \"{b['text']}\"")
        elif b["kind"] == "action":
            lines.append(f"[{b['id']}] {timing} ACTION: {b['text']}")
        elif b["kind"] == "sfx":
            lines.append(f"[{b['id']}] {timing} SFX: {b['text']}")

    return "\n".join(lines)


def propose_candidates(
    episode_data: Dict[str, Any], provider: Optional[str] = None, model: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Send episode beats to LLM, receive beat-ID ranges, and convert IDs to timestamps."""
    beats = episode_data["beats"]
    if not beats:
        return []

    beat_map = {b["id"]: b for b in beats}
    beat_order = {b["id"]: idx for idx, b in enumerate(beats)}

    prompt = build_beats_prompt(episode_data)
    response = complete_json(
        prompt=prompt,
        schema=PROPOSAL_SCHEMA,
        provider=provider,
        model=model,
    )

    raw_candidates = response.get("candidates", [])
    candidates: List[Dict[str, Any]] = []

    for raw in raw_candidates:
        s_id = raw.get("start_beat_id", "").strip()
        e_id = raw.get("end_beat_id", "").strip()
        h_id = raw.get("hook_beat_id", "").strip() or s_id
        c_id = raw.get("cliffhanger_beat_id", "").strip() or e_id
        rationale = raw.get("rationale", "").strip()

        # Resolve IDs
        if s_id not in beat_map or e_id not in beat_map:
            logger.warning(f"Proposed beat IDs not found: {s_id} -> {e_id}. Skipping.")
            continue

        # Ensure start precedes or equals end
        if beat_order[s_id] > beat_order[e_id]:
            s_id, e_id = e_id, s_id

        start_beat = beat_map[s_id]
        end_beat = beat_map[e_id]
        hook_beat = beat_map.get(h_id, start_beat)
        cliff_beat = beat_map.get(c_id, end_beat)

        start_sec = start_beat["start"]
        end_sec = end_beat["end"]
        raw_dur = round(end_sec - start_sec, 2)

        candidates.append(
            {
                "episode": episode_data["episode"],
                "start_beat_id": s_id,
                "end_beat_id": e_id,
                "hook_beat_id": hook_beat["id"],
                "cliffhanger_beat_id": cliff_beat["id"],
                "start_time": start_sec,
                "end_time": end_sec,
                "duration": raw_dur,
                "hook_text": hook_beat.get("text", ""),
                "cliffhanger_text": cliff_beat.get("text", ""),
                "rationale": rationale,
            }
        )

    return candidates
