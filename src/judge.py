"""Cold-viewer judge evaluating promo candidates.

Simulates a cold mobile viewer scrolling TikTok/Instagram:
- Sees ONLY the clip transcript plus a 15-second post-clip peek.
- Applies hard pass/fail gates: Hook, Cliffhanger, Standalone Coherence.
- Produces listwise rankings with conversion rationale and spoiler notes.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from src.llm import complete_json
from src.parser import format_timestamp

logger = logging.getLogger("src.judge")

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "hook_passed": {"type": "boolean"},
        "cliffhanger_passed": {"type": "boolean"},
        "standalone_passed": {"type": "boolean"},
        "hook_score": {"type": "number"},
        "cliffhanger_score": {"type": "number"},
        "standalone_score": {"type": "number"},
        "hook_critique": {"type": "string"},
        "cliffhanger_critique": {"type": "string"},
        "standalone_critique": {"type": "string"},
        "rationale": {"type": "string"},
        "spoiler_note": {"type": "string"},
    },
    "required": [
        "verdict",
        "hook_passed",
        "cliffhanger_passed",
        "standalone_passed",
        "hook_score",
        "cliffhanger_score",
        "standalone_score",
        "rationale",
    ],
}

LISTWISE_RANKING_SCHEMA = {
    "type": "object",
    "properties": {
        "rankings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "integer"},
                    "rank": {"type": "integer"},
                    "composite_score": {"type": "number"},
                    "rationale": {"type": "string"},
                    "spoiler_note": {"type": "string"},
                },
                "required": ["candidate_id", "rank", "composite_score", "rationale"],
            },
        }
    },
    "required": ["rankings"],
}


def build_cold_clip_transcript(
    candidate: Dict[str, Any], all_beats: List[Dict[str, Any]], peek_window_sec: float = 15.0
) -> Tuple[str, str]:
    """Generate the clip transcript and subsequent 15s peek without earlier context."""
    clip_start = candidate["start_time"]
    clip_end = candidate["end_time"]
    peek_end = clip_end + peek_window_sec

    clip_lines = []
    peek_lines = []

    for b in all_beats:
        timing = f"({format_timestamp(b['start'])} - {format_timestamp(b['end'])})"
        rel_start = round(b["start"] - clip_start, 2)
        rel_end = round(b["end"] - clip_start, 2)
        rel_time = f"[{rel_start:.1f}s - {rel_end:.1f}s]"

        if b["kind"] == "dialogue":
            line = f"{rel_time} {b['speaker']}: \"{b['text']}\""
        elif b["kind"] == "action":
            line = f"{rel_time} ACTION: {b['text']}"
        elif b["kind"] == "sfx":
            line = f"{rel_time} SFX: {b['text']}"
        else:
            line = f"{rel_time} {b.get('text', '')}"

        if b["start"] >= clip_start - 0.1 and b["end"] <= clip_end + 0.1:
            clip_lines.append(line)
        elif b["start"] > clip_end - 0.1 and b["start"] <= peek_end:
            peek_lines.append(line)

    return "\n".join(clip_lines), "\n".join(peek_lines)


def judge_single_candidate(
    candidate: Dict[str, Any],
    all_beats: List[Dict[str, Any]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Run cold-viewer gate check on a single candidate clip."""
    clip_text, peek_text = build_cold_clip_transcript(candidate, all_beats)

    prompt = f"""You are a ruthless short-form video ads judge for mobile apps (TikTok, Reels, YouTube Shorts).
You have NEVER seen this show before. You are seeing ONLY this candidate promo clip, followed by a 15-second peek of what happens immediately after the cut.

CANDIDATE PROMO CLIP DURATION: {candidate['duration']:.1f} seconds
CLIP TRANSCRIPT (timestamps relative to clip start):
{clip_text}

--- PEEK AT NEXT 15 SECONDS AFTER CUT ---
{peek_text if peek_text else '[End of episode]'}

EVALUATION GATES (Hard Pass/Fail):
1. HOOK GATE (0-10): Does something shocking, high-conflict, or curiosity-inducing happen in the first 3 seconds (0.0s - 3.0s)? Pass if >= 6.5.
2. CLIFFHANGER GATE (0-10): Does the clip cut right at an unresolved peak of dramatic tension, forcing the viewer to watch the show? (Verify against the 15s peek: if the tension was already resolved before the cut, FAIL). Pass if >= 6.5.
3. STANDALONE COHERENCE GATE (0-10): Can someone with zero show context understand who is attacking/betraying whom? Pass if >= 6.5.

Output JSON with your verdict ('PASS' only if all three gates pass, else 'FAIL'), individual scores, rationale, and a spoiler note."""

    judge_provider = provider or os.getenv("JUDGE_PROVIDER") or os.getenv("LLM_PROVIDER") or "mock"
    judge_model = model or os.getenv("JUDGE_MODEL")

    response = complete_json(
        prompt=prompt,
        schema=GATE_SCHEMA,
        provider=judge_provider,
        model=judge_model,
    )

    verdict = response.get("verdict", "PASS")
    h_pass = response.get("hook_passed", True)
    c_pass = response.get("cliffhanger_passed", True)
    s_pass = response.get("standalone_passed", True)
    overall_pass = (verdict == "PASS") and h_pass and c_pass and s_pass

    h_score = float(response.get("hook_score", 8.0))
    c_score = float(response.get("cliffhanger_score", 8.0))
    s_score = float(response.get("standalone_score", 8.0))

    composite = round(0.35 * h_score + 0.35 * c_score + 0.30 * s_score, 2)

    judge_meta = response.get("_metadata", {})

    return {
        **candidate,
        "verdict": "PASS" if overall_pass else "FAIL",
        "hook_passed": h_pass,
        "cliffhanger_passed": c_pass,
        "standalone_passed": s_pass,
        "hook_score": h_score,
        "cliffhanger_score": c_score,
        "standalone_score": s_score,
        "composite_score": composite,
        "judge_rationale": response.get("rationale", candidate.get("rationale", "")),
        "spoiler_note": response.get("spoiler_note", "No critical spoiler identified."),
        "judge_metadata": judge_meta,
    }


def build_batch_judge_prompt(
    candidates_batch: List[Dict[str, Any]], episodes_map: Dict[int, Dict[str, Any]]
) -> str:
    """Build a cold judge prompt evaluating multiple candidate clips in a single call."""
    lines = [
        "You are a ruthless short-form video ads judge for mobile apps (TikTok, Reels, YouTube Shorts).",
        "You have NEVER seen this show before. For each clip below, you see ONLY its transcript and a 15-second post-cut peek.",
        "CRITICAL INSTRUCTION: Judge EACH clip independently on its own merits without letting other clips in the list influence its score.",
        "",
        "EVALUATION GATES (Hard Pass/Fail):",
        "1. HOOK GATE (0-10): Does something shocking, high-conflict, or curiosity-inducing happen in the first 3 seconds (0.0s - 3.0s)? Pass if >= 6.5.",
        "2. CLIFFHANGER GATE (0-10): Does the clip cut right at an unresolved peak of dramatic tension? (Verify against the 15s peek: if the tension deflated before the cut, FAIL). Pass if >= 6.5.",
        "3. STANDALONE COHERENCE (0-10): Can someone with zero show context understand who is attacking/betraying whom? Pass if >= 6.5.",
        "",
        "REQUIRED JSON OUTPUT SCHEMA:",
        "{",
        '  "evaluations": [',
        "    {",
        '      "clip_id": "<string matching input clip ID>",',
        '      "verdict": "PASS" or "FAIL",',
        '      "hook_passed": <bool>,',
        '      "cliffhanger_passed": <bool>,',
        '      "standalone_passed": <bool>,',
        '      "hook_score": <float 0-10>,',
        '      "cliffhanger_score": <float 0-10>,',
        '      "standalone_score": <float 0-10>,',
        '      "rationale": "<1-line converting rationale>",',
        '      "spoiler_note": "<string>"',
        "    }",
        "  ]",
        "}",
        "",
        "CLIPS TO EVALUATE:",
    ]
    for c in candidates_batch:
        ep_num = c["episode"]
        ep_beats = episodes_map[ep_num]["beats"]
        clip_text, peek_text = build_cold_clip_transcript(c, ep_beats)
        lines.append(f"--- CANDIDATE CLIP [ID: {c['clip_id']}] (Episode {ep_num}, Duration: {c['duration']:.1f}s) ---")
        lines.append(f"CLIP TRANSCRIPT (relative timestamps):\n{clip_text}")
        lines.append(f"PEEK AT NEXT 15s AFTER CUT:\n{peek_text if peek_text else '[End of episode]'}")
        lines.append("")

    return "\n".join(lines)


def judge_batch_candidates(
    candidates_batch: List[Dict[str, Any]],
    episodes_map: Dict[int, Dict[str, Any]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Judge a batch of promo candidates in a single LLM call."""
    for i, c in enumerate(candidates_batch, 1):
        c.setdefault("clip_id", f"C{c['episode']:02d}_{i:02d}")

    prompt = build_batch_judge_prompt(candidates_batch, episodes_map)
    response = complete_json(
        prompt=prompt,
        provider=provider,
        model=model,
    )

    judge_meta = response.get("_metadata", {})
    evals = response.get("evaluations", [])
    if isinstance(evals, dict):
        evals = [evals]
    elif not isinstance(evals, list):
        evals = []

    eval_map = {e.get("clip_id"): e for e in evals if isinstance(e, dict) and "clip_id" in e}

    judged_list = []
    for c in candidates_batch:
        e = eval_map.get(c["clip_id"], {})
        verdict = e.get("verdict", "PASS")
        h_pass = e.get("hook_passed", True)
        c_pass = e.get("cliffhanger_passed", True)
        s_pass = e.get("standalone_passed", True)
        overall_pass = (verdict == "PASS") and h_pass and c_pass and s_pass

        h_score = float(e.get("hook_score", 8.0))
        c_score = float(e.get("cliffhanger_score", 8.0))
        s_score = float(e.get("standalone_score", 8.0))
        composite = round(0.35 * h_score + 0.35 * c_score + 0.30 * s_score, 2)

        judged_list.append(
            {
                **c,
                "verdict": "PASS" if overall_pass else "FAIL",
                "hook_passed": h_pass,
                "cliffhanger_passed": c_pass,
                "standalone_passed": s_pass,
                "hook_score": h_score,
                "cliffhanger_score": c_score,
                "standalone_score": s_score,
                "composite_score": composite,
                "judge_rationale": e.get("rationale", c.get("rationale", "")),
                "spoiler_note": e.get("spoiler_note", "No critical spoiler identified."),
                "judge_metadata": judge_meta,
            }
        )

    return judged_list



def rank_survivors(
    survivors: List[Dict[str, Any]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Perform listwise comparison and global ranking on surviving promo candidates."""
    if not survivors:
        return []

    if len(survivors) == 1:
        survivors[0]["rank"] = 1
        return survivors

    # Sort survivors initially by composite score
    survivors.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)

    # Format summaries for listwise comparison
    summary_lines = []
    for idx, c in enumerate(survivors, 1):
        summary_lines.append(
            f"Candidate #{idx} (Episode {c['episode']}, {c['start_formatted']} - {c['end_formatted']}, {c['duration']}s): "
            f"Hook: '{c.get('hook_text', '')[:60]}...' | Cliffhanger: '{c.get('cliffhanger_text', '')[:60]}...' | "
            f"Scores: H={c.get('hook_score')}, C={c.get('cliffhanger_score')}, S={c.get('standalone_score')}"
        )

    prompt = f"""You are the Head of Growth & User Acquisition at Kuku.
Review these {len(survivors)} candidate microdrama promos that passed all quality filters:

{chr(10).join(summary_lines)}

TASK: Provide a final listwise ranking of which promo ads will drive the highest click-through rate (CTR) and app installs on TikTok/Instagram Reels.
Consider:
1. Pure stopping power and emotional hook intensity.
2. Narrative intrigue without giving away late-season climaxes (spoilers).
3. Pacing and punchiness.

Return a JSON array of rankings with candidate_id (1-indexed matching list above), rank (1 = best), composite_score (1-10), rationale, and spoiler_note."""

    judge_provider = provider or os.getenv("JUDGE_PROVIDER") or os.getenv("LLM_PROVIDER") or "mock"
    judge_model = model or os.getenv("JUDGE_MODEL")

    try:
        response = complete_json(
            prompt=prompt,
            schema=LISTWISE_RANKING_SCHEMA,
            provider=judge_provider,
            model=judge_model,
        )
        rankings = response.get("rankings", [])
        rank_dict = {r["candidate_id"]: r for r in rankings if "candidate_id" in r}

        for idx, cand in enumerate(survivors, 1):
            if idx in rank_dict:
                cand["rank"] = rank_dict[idx].get("rank", idx)
                cand["rank_rationale"] = rank_dict[idx].get("rationale", cand.get("judge_rationale", ""))
                cand["spoiler_note"] = rank_dict[idx].get("spoiler_note", cand.get("spoiler_note", ""))
                if "composite_score" in rank_dict[idx]:
                    cand["composite_score"] = float(rank_dict[idx]["composite_score"])
            else:
                cand["rank"] = idx

        survivors.sort(key=lambda x: x.get("rank", 999))
    except Exception as e:
        logger.warning(f"Listwise ranking failed ({e}), falling back to composite score sorting.")
        for idx, cand in enumerate(survivors, 1):
            cand["rank"] = idx

    return survivors
