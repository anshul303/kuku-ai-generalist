"""Keyword and regex heuristic baseline for promo detection.

Provides a fast, zero-cost rule-based baseline to benchmark against the AI pipeline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.parser import format_timestamp
from src.validate import validate_candidates

HOOK_KEYWORDS = re.compile(
    r"\b(slap|betray|marry|disown|bastard|shame|beg|kneel|leave|never|curse|outrage|shock|gasp|wedding|liar|cheat|traitor)\b",
    re.IGNORECASE,
)

CLIFF_KEYWORDS = re.compile(
    r"(\?|\!|cliffhanger|swells|cut to black|drone|ominous|gasp|defiance|unresolved)",
    re.IGNORECASE,
)


def score_beat_as_hook(beat: Dict[str, Any]) -> float:
    """Heuristic scoring for hook potential."""
    score = 0.0
    text = beat.get("text", "")
    emotion = beat.get("emotion") or ""

    if beat.get("kind") == "dialogue":
        score += 2.0
    elif beat.get("kind") == "action":
        score += 1.5

    # Check keywords in text and emotion
    score += len(HOOK_KEYWORDS.findall(text)) * 2.5
    score += len(HOOK_KEYWORDS.findall(emotion)) * 2.0

    if "!" in text or "?" in text:
        score += 1.0

    return score


def score_beat_as_cliffhanger(beat: Dict[str, Any]) -> float:
    """Heuristic scoring for cliffhanger potential."""
    score = 0.0
    text = beat.get("text", "")
    emotion = beat.get("emotion") or ""

    if beat.get("kind") == "sfx":
        score += 3.0

    score += len(CLIFF_KEYWORDS.findall(text)) * 2.0
    score += len(CLIFF_KEYWORDS.findall(emotion)) * 1.5

    if "?" in text:
        score += 2.5
    elif "..." in text or "—" in text:
        score += 1.5

    return score


def find_baseline_promos(episode_data: Dict[str, Any], max_promos: int = 3) -> List[Dict[str, Any]]:
    """Generate baseline promo clips using heuristic keyword scoring."""
    beats = episode_data["beats"]
    if not beats:
        return []

    # Score all beats for hooks and cliffhangers
    hook_scores = [score_beat_as_hook(b) for b in beats]
    cliff_scores = [score_beat_as_cliffhanger(b) for b in beats]

    raw_candidates = []

    # Find top hook indices
    sorted_hook_indices = sorted(range(len(beats)), key=lambda i: hook_scores[i], reverse=True)

    used_starts = set()
    for h_idx in sorted_hook_indices:
        if len(raw_candidates) >= max_promos:
            break
        if h_idx in used_starts:
            continue

        # Look forward for a strong cliffhanger beat 20s to 55s ahead
        best_c_idx = None
        best_c_score = -1.0
        h_start = beats[h_idx]["start"]

        for c_idx in range(h_idx, len(beats)):
            duration = beats[c_idx]["end"] - h_start
            if duration > 58.0:
                break
            if duration >= 18.0:
                c_score = cliff_scores[c_idx]
                if c_score > best_c_score:
                    best_c_score = c_score
                    best_c_idx = c_idx

        if best_c_idx is not None:
            raw_candidates.append(
                {
                    "episode": episode_data["episode"],
                    "start_beat_id": beats[h_idx]["id"],
                    "end_beat_id": beats[best_c_idx]["id"],
                    "hook_beat_id": beats[h_idx]["id"],
                    "cliffhanger_beat_id": beats[best_c_idx]["id"],
                    "start_time": h_start,
                    "end_time": beats[best_c_idx]["end"],
                    "duration": round(beats[best_c_idx]["end"] - h_start, 2),
                    "hook_text": beats[h_idx]["text"],
                    "cliffhanger_text": beats[best_c_idx]["text"],
                    "rationale": f"Heuristic baseline match (Hook score: {hook_scores[h_idx]:.1f}, Cliff score: {best_c_score:.1f})",
                }
            )
            used_starts.add(h_idx)

    return validate_candidates(raw_candidates, beats)
