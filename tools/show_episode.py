"""Compact Screenplay Timeline Viewer.

Prints episode N as a clean chronological timeline with timestamps, speakers,
and camera shot cut boundaries. Strictly reads raw screenplay data only;
does not read or display any pipeline outputs, scores, or suggestions.

Usage:
    python tools/show_episode.py <episode_number>
    python tools/show_episode.py 45
"""

from __future__ import annotations

import glob
import os
import sys

from src.parser import format_timestamp, parse_episode_file


def show_episode_timeline(
    ep_num: int,
    assets_dir: str = "assets/I Married a Broken Soldier. He was a Duke",
):
    matches = glob.glob(os.path.join(assets_dir, f"episode-{ep_num:03d}*.txt"))
    if not matches:
        print(f"Error: Screenplay for Episode {ep_num} not found in '{assets_dir}'.")
        sys.exit(1)

    filepath = matches[0]
    ep_data = parse_episode_file(filepath)

    print("=" * 80)
    print(f"🎬 EPISODE {ep_data['episode']:02d} — COMPACT TIMELINE")
    if ep_data.get("logline"):
        print(f"Logline: {ep_data['logline']}")
    print(f"Source: {os.path.basename(filepath)}")
    print("=" * 80)

    # Interleave shots and beats chronologically
    events = []

    for shot in ep_data.get("shots", []):
        events.append(
            {
                "time": shot["start"],
                "type": "SHOT",
                "start": shot["start"],
                "end": shot["end"],
                "desc": shot.get("desc", ""),
            }
        )

    for beat in ep_data.get("beats", []):
        events.append(
            {
                "time": beat["start"],
                "type": "BEAT",
                "id": beat["id"],
                "start": beat["start"],
                "end": beat["end"],
                "kind": beat["kind"],
                "speaker": beat.get("speaker"),
                "emotion": beat.get("emotion"),
                "text": beat["text"],
            }
        )

    # Stable sort by timestamp, prioritizing shots that start at the exact same time
    events.sort(key=lambda x: (x["time"], 0 if x["type"] == "SHOT" else 1))

    for ev in events:
        if ev["type"] == "SHOT":
            s_str = format_timestamp(ev["start"])
            e_str = format_timestamp(ev["end"])
            print(f"\n🎥 [SHOT BOUNDARY: {s_str} - {e_str}] {ev['desc']}")
        else:
            s_str = format_timestamp(ev["start"])
            e_str = format_timestamp(ev["end"])
            b_id = ev["id"]
            kind = ev["kind"]

            if kind == "dialogue":
                emo_str = f" ({ev['emotion']})" if ev["emotion"] else ""
                print(f"  {s_str} - {e_str} | [{b_id}] {ev['speaker']}{emo_str}: \"{ev['text']}\"")
            elif kind == "action":
                print(f"  {s_str} - {e_str} | [{b_id}] ACTION: {ev['text']}")
            elif kind == "sfx":
                print(f"  {s_str} - {e_str} | [{b_id}] SFX: {ev['text']}")

    print("\n" + "=" * 80)
    total_beats = len(ep_data.get("beats", []))
    total_shots = len(ep_data.get("shots", []))
    final_time = format_timestamp(ep_data["beats"][-1]["end"]) if ep_data.get("beats") else "00:00.00"
    print(f"End of Episode {ep_num:02d} | Duration: {final_time} | Beats: {total_beats} | Shots: {total_shots}")
    print("=" * 80 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/show_episode.py <episode_number>")
        print("Example: python tools/show_episode.py 45")
        sys.exit(1)

    try:
        ep_num = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid episode number '{sys.argv[1]}'. Must be an integer.")
        sys.exit(1)

    show_episode_timeline(ep_num)


if __name__ == "__main__":
    main()
