"""Validation and repair engine for promo candidates.

Enforces:
- Strict 20.0s - 60.0s duration by adding/trimming whole beats
- Hook beat occurs within 3.0s of clip start
- Boundary cuts only at whole beat boundaries (no mid-line cuts)
- Overlap deduplication
- Complete repair audit logging
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.parser import format_timestamp

logger = logging.getLogger("src.validate")

MIN_DURATION_SEC = 20.0
MAX_DURATION_SEC = 60.0
MAX_HOOK_OFFSET_SEC = 3.0
OVERLAP_DEDUPE_THRESHOLD = 0.70


def compute_interval_overlap(s1: float, e1: float, s2: float, e2: float) -> float:
    """Calculate Intersection over Union (IoU) of two time intervals."""
    intersection = max(0.0, min(e1, e2) - max(s1, s2))
    union = max(e1, e2) - min(s1, s2)
    if union <= 0.0:
        return 0.0
    return intersection / union


def validate_and_repair_candidate(
    candidate: Dict[str, Any],
    all_beats: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Validate and deterministically repair a candidate promo clip.

    Returns the repaired candidate dict with 'repairs' list, or None if irrecoverable.
    """
    beat_map = {b["id"]: b for b in all_beats}
    beat_indices = {b["id"]: idx for idx, b in enumerate(all_beats)}

    s_id = candidate["start_beat_id"]
    e_id = candidate["end_beat_id"]
    h_id = candidate.get("hook_beat_id", s_id)
    c_id = candidate.get("cliffhanger_beat_id", e_id)

    if s_id not in beat_indices or e_id not in beat_indices:
        logger.warning(f"Invalid beat IDs in candidate: {s_id}, {e_id}")
        return None

    s_idx = beat_indices[s_id]
    e_idx = beat_indices[e_id]
    h_idx = beat_indices.get(h_id, s_idx)
    c_idx = beat_indices.get(c_id, e_idx)

    repairs: List[str] = []

    # 1. Enforce hook within 3.0s of clip start
    hook_offset = beat_map[all_beats[h_idx]["id"]]["start"] - beat_map[all_beats[s_idx]["id"]]["start"]
    if hook_offset > MAX_HOOK_OFFSET_SEC:
        old_s_id = all_beats[s_idx]["id"]
        # Advance s_idx toward h_idx until hook_offset <= 3.0s
        while s_idx < h_idx and (all_beats[h_idx]["start"] - all_beats[s_idx]["start"]) > MAX_HOOK_OFFSET_SEC:
            s_idx += 1
        new_s_id = all_beats[s_idx]["id"]
        repairs.append(
            f"ADVANCE_START: Shifted start from {old_s_id} to {new_s_id} so hook offset is "
            f"{all_beats[h_idx]['start'] - all_beats[s_idx]['start']:.2f}s (<= {MAX_HOOK_OFFSET_SEC}s)"
        )

    # 2. Check and repair duration < 20.0s by adding subsequent beats
    curr_duration = all_beats[e_idx]["end"] - all_beats[s_idx]["start"]
    if curr_duration < MIN_DURATION_SEC:
        orig_dur = curr_duration
        added_beats = []
        while curr_duration < MIN_DURATION_SEC and e_idx < len(all_beats) - 1:
            e_idx += 1
            added_beats.append(all_beats[e_idx]["id"])
            curr_duration = all_beats[e_idx]["end"] - all_beats[s_idx]["start"]

        # If still under 20s and we can expand backwards without pushing hook past 3s
        while (
            curr_duration < MIN_DURATION_SEC
            and s_idx > 0
            and (all_beats[h_idx]["start"] - all_beats[s_idx - 1]["start"]) <= MAX_HOOK_OFFSET_SEC
        ):
            s_idx -= 1
            added_beats.append(all_beats[s_idx]["id"])
            curr_duration = all_beats[e_idx]["end"] - all_beats[s_idx]["start"]

        if added_beats:
            repairs.append(
                f"EXPAND_DURATION: Added {len(added_beats)} beat(s) ({added_beats[0]}..{added_beats[-1]}) "
                f"to increase duration from {orig_dur:.1f}s to {curr_duration:.1f}s"
            )

    # 3. Check and repair duration > 60.0s by trimming trailing beats
    curr_duration = all_beats[e_idx]["end"] - all_beats[s_idx]["start"]
    if curr_duration > MAX_DURATION_SEC:
        orig_dur = curr_duration
        trimmed_beats = []
        while curr_duration > MAX_DURATION_SEC and e_idx > s_idx:
            trimmed_beats.append(all_beats[e_idx]["id"])
            e_idx -= 1
            curr_duration = all_beats[e_idx]["end"] - all_beats[s_idx]["start"]

        if trimmed_beats:
            repairs.append(
                f"TRIM_DURATION: Trimmed {len(trimmed_beats)} trailing beat(s) "
                f"to reduce duration from {orig_dur:.1f}s to {curr_duration:.1f}s"
            )

    # Final check on duration
    final_start = all_beats[s_idx]["start"]
    final_end = all_beats[e_idx]["end"]
    final_duration = round(final_end - final_start, 2)

    if final_duration < MIN_DURATION_SEC or final_duration > MAX_DURATION_SEC:
        repairs.append(
            f"REJECTED: Unable to satisfy duration constraint (final duration: {final_duration:.1f}s)"
        )
        logger.warning(f"Candidate rejected: duration {final_duration:.1f}s outside bounds [20, 60]")
        return None

    # Update cliffhanger beat if trimmed past it
    if c_idx > e_idx:
        c_idx = e_idx
        repairs.append(f"ADJUST_CLIFFHANGER: Set cliffhanger beat to final clip beat {all_beats[e_idx]['id']}")

    return {
        "episode": candidate["episode"],
        "start_beat_id": all_beats[s_idx]["id"],
        "end_beat_id": all_beats[e_idx]["id"],
        "hook_beat_id": all_beats[h_idx]["id"],
        "cliffhanger_beat_id": all_beats[c_idx]["id"],
        "start_time": final_start,
        "end_time": final_end,
        "duration": final_duration,
        "start_formatted": format_timestamp(final_start),
        "end_formatted": format_timestamp(final_end),
        "hook_text": all_beats[h_idx].get("text", ""),
        "cliffhanger_text": all_beats[c_idx].get("text", ""),
        "rationale": candidate.get("rationale", ""),
        "repairs": repairs,
    }


def deduplicate_candidates(candidates: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Deduplicate candidates with significant temporal overlap (> 70% IoU)."""
    if not candidates:
        return [], []

    deduped: List[Dict[str, Any]] = []
    dropped_logs: List[str] = []

    for cand in candidates:
        is_dup = False
        for kept in deduped:
            iou = compute_interval_overlap(
                cand["start_time"], cand["end_time"], kept["start_time"], kept["end_time"]
            )
            if iou >= OVERLAP_DEDUPE_THRESHOLD:
                is_dup = True
                dropped_logs.append(
                    f"DEDUPE: Dropped {cand['start_beat_id']}..{cand['end_beat_id']} "
                    f"due to {iou:.1%} overlap with {kept['start_beat_id']}..{kept['end_beat_id']}"
                )
                break
        if not is_dup:
            deduped.append(cand)

    return deduped, dropped_logs


def validate_candidates(
    raw_candidates: List[Dict[str, Any]], all_beats: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Run full validation, repair, and deduplication pipeline on candidate list."""
    validated: List[Dict[str, Any]] = []

    for cand in raw_candidates:
        repaired = validate_and_repair_candidate(cand, all_beats)
        if repaired:
            validated.append(repaired)

    deduped, dedupe_logs = deduplicate_candidates(validated)
    for cand in deduped:
        if dedupe_logs:
            cand.setdefault("repairs", []).extend([d for d in dedupe_logs if cand["start_beat_id"] in d])

    return deduped
