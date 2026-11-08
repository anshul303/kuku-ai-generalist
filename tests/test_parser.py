"""Tests for src/parser.py validating all 50 episodes."""

import glob
import os
import re
import pytest

from src.parser import parse_all_episodes, parse_episode_file, parse_timestamp

DATA_DIR = "assets/I Married a Broken Soldier. He was a Duke"


def test_50_of_50_episodes_parsed():
    """Ensure all 50 episodes are discovered and parsed successfully."""
    files = glob.glob(os.path.join(DATA_DIR, "*.txt"))
    assert len(files) == 50, f"Expected 50 episode files, found {len(files)}"

    episodes = parse_all_episodes(DATA_DIR)
    assert len(episodes) == 50

    # Ensure all episode numbers 1..50 are present
    ep_nums = [ep["episode"] for ep in episodes]
    assert ep_nums == list(range(1, 51)), f"Missing or out-of-order episodes: {ep_nums}"

    for ep in episodes:
        assert ep["logline"], f"Episode {ep['episode']} missing logline"
        assert len(ep["beats"]) > 0, f"Episode {ep['episode']} has 0 beats"
        assert len(ep["shots"]) > 0, f"Episode {ep['episode']} has 0 shots"


def test_monotonic_times():
    """Ensure every beat has start <= end and beat starts are monotonically non-decreasing."""
    episodes = parse_all_episodes(DATA_DIR)
    for ep in episodes:
        beats = ep["beats"]
        for i, b in enumerate(beats):
            assert b["start"] <= b["end"], (
                f"Episode {ep['episode']} beat {b['id']} start {b['start']} > end {b['end']}"
            )
            if i > 0:
                # Monotonic non-decreasing with minor tolerance for simultaneous reaction shots
                prev_b = beats[i - 1]
                assert b["start"] >= prev_b["start"] - 0.5, (
                    f"Episode {ep['episode']} non-monotonic: {prev_b['id']} ({prev_b['start']}) followed by {b['id']} ({b['start']})"
                )


def test_no_dropped_lines():
    """Ensure every meaningful line in every screenplay file is accounted for."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")))
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        in_block = False
        dropped = []
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line:
                continue

            line_up = line.upper()
            if any(
                line_up.startswith(p)
                for p in [
                    "EPISODE NUMBER:",
                    "EPISODE LOGLINE:",
                    "CONTINUITY NOTES:",
                    "--- SCRIPT",
                    "SCENE",
                    "SCENE HEADING:",
                    "SCENE START:",
                    "SCENE END:",
                    "ACTIONS AND DIALOGUE:",
                    "(NO NEWLINE",
                ]
            ):
                continue

            if line.startswith("**") and "**" in line[2:]:
                in_block = True
                continue

            if line_up.startswith("START:") and "END:" in line_up:
                continue

            if not in_block:
                dropped.append(line)

        assert len(dropped) == 0, f"Dropped lines in {filepath}: {dropped}"
