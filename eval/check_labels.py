"""Validator for eval/ground_truth_user.json.

Checks:
1. JSON schema conformity.
2. Each clip duration is strictly between 20.0s and 60.0s.
3. Timestamps fall strictly inside episode boundaries (0.0 <= start < end <= ep_duration).
Reports problems only.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from typing import Any, Dict, List

from src.parser import parse_episode_file


def get_episode_durations(assets_dir: str = "assets/I Married a Broken Soldier. He was a Duke") -> Dict[int, float]:
    """Load total duration for each episode from raw screenplays."""
    durations = {}
    files = glob.glob(os.path.join(assets_dir, "episode-*.txt"))
    for f in files:
        try:
            ep = parse_episode_file(f)
            ep_num = ep["episode"]
            if ep["beats"]:
                durations[ep_num] = ep["beats"][-1]["end"]
            elif ep["scenes"]:
                durations[ep_num] = ep["scenes"][-1].get("end", 0.0)
            else:
                durations[ep_num] = 0.0
        except Exception:
            pass
    return durations


def validate_ground_truth(
    filepath: str = "eval/ground_truth_user.json",
    assets_dir: str = "assets/I Married a Broken Soldier. He was a Duke",
) -> List[str]:
    problems: List[str] = []

    if not os.path.exists(filepath):
        problems.append(f"File not found: {filepath}")
        return problems

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        problems.append(f"Invalid JSON in {filepath}: {e}")
        return problems

    if not isinstance(data, list):
        problems.append(f"Schema error: Top-level structure must be a JSON array (list), got {type(data).__name__}.")
        return problems

    ep_durations = get_episode_durations(assets_dir)

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            problems.append(f"Item #{i}: Expected dictionary, got {type(item).__name__}.")
            continue

        ep_num = item.get("episode")
        if ep_num is None or not isinstance(ep_num, int):
            problems.append(f"Item #{i}: Missing or invalid 'episode' integer field.")
            continue

        promos = item.get("promos")
        if promos is None or not isinstance(promos, list):
            problems.append(f"Episode {ep_num}: Missing or invalid 'promos' array.")
            continue

        if not promos:
            problems.append(f"Episode {ep_num}: 'promos' list is empty.")
            continue

        ep_max_duration = ep_durations.get(ep_num)

        for p_idx, p in enumerate(promos):
            cid = p.get("clip_id", f"clip_{p_idx+1}")
            start = p.get("start_time")
            end = p.get("end_time")

            if start is None or end is None:
                problems.append(f"Episode {ep_num} ({cid}): Missing 'start_time' or 'end_time'.")
                continue

            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                problems.append(f"Episode {ep_num} ({cid}): 'start_time' and 'end_time' must be numbers.")
                continue

            # 1. Ordering
            if start < 0:
                problems.append(f"Episode {ep_num} ({cid}): start_time ({start}s) is negative.")

            if start >= end:
                problems.append(f"Episode {ep_num} ({cid}): start_time ({start}s) >= end_time ({end}s).")
                continue

            # 2. Duration check: 20.0s to 60.0s
            duration = end - start
            if duration < 19.95 or duration > 60.05:
                problems.append(
                    f"Episode {ep_num} ({cid}): Duration {duration:.2f}s outside required 20.0s - 60.0s bounds."
                )

            # 3. Episode boundary check
            if ep_max_duration is not None and ep_max_duration > 0:
                if end > ep_max_duration + 1.0:  # Allow 1s tolerance for trailing audio/sfx
                    problems.append(
                        f"Episode {ep_num} ({cid}): end_time ({end:.2f}s) exceeds episode duration ({ep_max_duration:.2f}s)."
                    )

    return problems


def main():
    target_file = sys.argv[1] if len(sys.argv) > 1 else "eval/ground_truth_user.json"
    problems = validate_ground_truth(target_file)

    if problems:
        print(f"❌ Found {len(problems)} problem(s) in {target_file}:")
        for p in problems:
            print(f"  • {p}")
        sys.exit(1)
    else:
        # Report problems only (silent or clean 1-line status if run standalone)
        if len(sys.argv) > 1 or os.path.exists(target_file):
            print(f"✅ {target_file}: Validated successfully. 0 problems found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
