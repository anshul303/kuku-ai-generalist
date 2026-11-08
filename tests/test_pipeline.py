"""Tests for proposal, validation, and evaluation pipeline."""

import pytest
from src.parser import parse_episode_file
from src.propose import propose_candidates
from src.validate import validate_candidates, validate_and_repair_candidate
from src.judge import judge_single_candidate

EP1_PATH = "assets/I Married a Broken Soldier. He was a Duke/episode-001-Episode 1671703.txt"


def test_validation_bounds():
    ep = parse_episode_file(EP1_PATH)
    beats = ep["beats"]

    # Candidate with duration under 20s
    short_cand = {
        "episode": 1,
        "start_beat_id": beats[0]["id"],
        "end_beat_id": beats[1]["id"],
        "hook_beat_id": beats[0]["id"],
        "cliffhanger_beat_id": beats[1]["id"],
        "rationale": "Test candidate",
    }
    repaired = validate_and_repair_candidate(short_cand, beats)
    assert repaired is not None
    assert 20.0 <= repaired["duration"] <= 60.0
    assert len(repaired["repairs"]) > 0


def test_hook_offset_enforcement():
    ep = parse_episode_file(EP1_PATH)
    beats = ep["beats"]

    # Force hook beat to be way later than start beat
    late_hook_cand = {
        "episode": 1,
        "start_beat_id": beats[0]["id"],
        "end_beat_id": beats[10]["id"],
        "hook_beat_id": beats[5]["id"],  # Beats[5] is > 3s after start
        "cliffhanger_beat_id": beats[10]["id"],
        "rationale": "Late hook test",
    }
    repaired = validate_and_repair_candidate(late_hook_cand, beats)
    assert repaired is not None
    # Verify hook offset is <= 3.0s
    hook_beat = next(b for b in beats if b["id"] == repaired["hook_beat_id"])
    assert hook_beat["start"] - repaired["start_time"] <= 3.0


def test_cold_viewer_judge():
    ep = parse_episode_file(EP1_PATH)
    beats = ep["beats"]

    cand = {
        "episode": 1,
        "start_beat_id": beats[1]["id"],
        "end_beat_id": beats[12]["id"],
        "hook_beat_id": beats[1]["id"],
        "cliffhanger_beat_id": beats[12]["id"],
        "start_time": beats[1]["start"],
        "end_time": beats[12]["end"],
        "duration": round(beats[12]["end"] - beats[1]["start"], 2),
        "hook_text": beats[1]["text"],
        "cliffhanger_text": beats[12]["text"],
        "rationale": "Altar confrontation",
    }

    judged = judge_single_candidate(cand, beats, provider="mock")
    assert "verdict" in judged
    assert "hook_passed" in judged
    assert "composite_score" in judged
    assert judged["composite_score"] >= 0.0
