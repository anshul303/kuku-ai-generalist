"""Screenplay parser for microdrama episodes.

Parses screenplays into structured JSON with:
- episode metadata (number, logline, continuity notes)
- scenes (heading, start, end)
- beats (dialogue, action, sfx with ID, timestamps, speaker, emotion, text)
- shots (camera descriptions, start, end)
"""

from __future__ import annotations

import glob
import os
import re
from typing import Any, Dict, List, Optional, Tuple


def parse_timestamp(ts_str: str) -> float:
    """Convert 'MM:SS.SS' or 'SS.SS' string into float seconds."""
    ts_str = ts_str.strip().strip("()")
    parts = ts_str.split(":")
    if len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        return round(minutes * 60 + seconds, 2)
    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return round(hours * 3600 + minutes * 60 + seconds, 2)
    elif len(parts) == 1:
        return round(float(parts[0]), 2)
    raise ValueError(f"Invalid timestamp format: {ts_str}")


def format_timestamp(seconds: float) -> str:
    """Convert float seconds into 'MM:SS.SS' string."""
    seconds = max(0.0, seconds)
    minutes = int(seconds // 60)
    rem_seconds = seconds - (minutes * 60)
    return f"{minutes:02d}:{rem_seconds:05.2f}"


def extract_header_fields(text: str) -> Tuple[int, str, str, str]:
    """Extract episode number, logline, continuity, and script body."""
    ep_num = 0
    logline = ""
    continuity = ""

    ep_match = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", text, re.IGNORECASE)
    if ep_match:
        ep_num = int(ep_match.group(1))

    logline_match = re.search(
        r"EPISODE LOGLINE:\s*(.*?)(?=\n[A-Z\s\-]+:|\n--- SCRIPT START ---|\nSCENE|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if logline_match:
        logline = " ".join(logline_match.group(1).split())

    cont_match = re.search(
        r"CONTINUITY NOTES:\s*(.*?)(?=\n--- SCRIPT START ---|\nSCENE|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if cont_match:
        continuity = " ".join(cont_match.group(1).split())

    # Find where script actually begins
    script_start_idx = 0
    start_marker = re.search(r"--- SCRIPT START ---", text, re.IGNORECASE)
    if start_marker:
        script_start_idx = start_marker.end()
    else:
        # Fallback to first SCENE marker
        scene_marker = re.search(r"\nSCENE\s+\d+", text, re.IGNORECASE)
        if scene_marker:
            script_start_idx = scene_marker.start()

    script_end_idx = len(text)
    end_marker = re.search(r"--- SCRIPT END ---", text, re.IGNORECASE)
    if end_marker:
        script_end_idx = end_marker.start()

    script_body = text[script_start_idx:script_end_idx]
    return ep_num, logline, continuity, script_body


def parse_speaker_and_emotion(tag: str) -> Tuple[str, Optional[str]]:
    """Parse dialogue header tag like '**MATRIARCH (Cold, Commanding):**' into speaker and emotion."""
    # Strip asterisks and trailing colons/spaces
    cleaned = tag.strip().strip("*").strip()
    emotions = re.findall(r"\((.*?)\)", cleaned)
    emotion_str = ", ".join(e.strip() for e in emotions if e.strip()) or None

    speaker = cleaned.split("(")[0].rstrip(":").strip()
    return speaker, emotion_str


def parse_episode_text(text: str, filename: str = "") -> Dict[str, Any]:
    """Parse raw episode text into the standardized dictionary format."""
    ep_num, logline, continuity, script_body = extract_header_fields(text)

    if ep_num == 0 and filename:
        # Infer episode number from filename if missing from text
        match = re.search(r"episode-?(\d+)", filename, re.IGNORECASE)
        if match:
            ep_num = int(match.group(1))

    # Extract scenes
    scenes: List[Dict[str, Any]] = []
    scene_matches = list(
        re.finditer(
            r"(SCENE\s+\d+)\s*\n"
            r"(?:Scene heading:\s*(.*?)\n)?"
            r"(?:Scene start:\s*([0-9:.]+)\n)?"
            r"(?:Scene end:\s*([0-9:.]+)\n)?",
            script_body,
            re.IGNORECASE,
        )
    )

    for m in scene_matches:
        scene_id = m.group(1).strip()
        heading = (m.group(2) or "").strip()
        st = parse_timestamp(m.group(3)) if m.group(3) else 0.0
        et = parse_timestamp(m.group(4)) if m.group(4) else 0.0
        scenes.append(
            {
                "scene_id": scene_id,
                "heading": heading,
                "start": st,
                "end": et,
            }
        )

    # Regex to identify blocks: **TAG** followed by Start/End line and text
    block_pattern = re.compile(
        r"(\*\*[^*]+\*\*)\s*\n"
        r"Start:\s*\(?([0-9:.]+)\)?\s*\|\s*End:\s*\(?([0-9:.]+)\)?\s*\n"
        r"(.*?)(?=(?:\n\*\*[^*]+\*\*|\nSCENE\s+\d+|\n--- SCRIPT END ---|\Z))",
        re.DOTALL | re.IGNORECASE,
    )

    beats: List[Dict[str, Any]] = []
    shots: List[Dict[str, Any]] = []

    beat_idx = 1
    for match in block_pattern.finditer(script_body):
        tag = match.group(1).strip()
        start_ts = parse_timestamp(match.group(2))
        end_ts = parse_timestamp(match.group(3))
        raw_text = match.group(4).strip()

        # Clean quotes and redundant whitespace from text
        cleaned_text = " ".join(raw_text.split())
        if cleaned_text.startswith('"') and cleaned_text.endswith('"') and len(cleaned_text) > 1:
            cleaned_text = cleaned_text[1:-1].strip()

        tag_upper = tag.upper()
        if "CAMERA" in tag_upper:
            shots.append(
                {
                    "start": start_ts,
                    "end": end_ts,
                    "desc": cleaned_text,
                }
            )
        else:
            beat_id = f"E{ep_num:02d}-B{beat_idx:03d}"
            beat_idx += 1

            if "ACTION" in tag_upper:
                kind = "action"
                speaker = None
                emotion = None
            elif any(k in tag_upper for k in ["SOUND FX", "SFX", "SOUND"]):
                kind = "sfx"
                speaker = None
                emotion = None
            else:
                kind = "dialogue"
                speaker, emotion = parse_speaker_and_emotion(tag)

            beats.append(
                {
                    "id": beat_id,
                    "kind": kind,
                    "speaker": speaker,
                    "emotion": emotion,
                    "start": start_ts,
                    "end": end_ts,
                    "text": cleaned_text,
                }
            )

    return {
        "episode": ep_num,
        "logline": logline,
        "continuity": continuity,
        "scenes": scenes,
        "beats": beats,
        "shots": shots,
    }


def parse_episode_file(filepath: str) -> Dict[str, Any]:
    """Parse a single episode file on disk."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_episode_text(content, filename=filename)


def parse_all_episodes(directory_path: str) -> List[Dict[str, Any]]:
    """Parse all episode text files in the given directory, sorted by episode number."""
    filepaths = sorted(glob.glob(os.path.join(directory_path, "*.txt")))
    parsed = [parse_episode_file(fp) for fp in filepaths]
    parsed.sort(key=lambda x: x["episode"])
    return parsed
