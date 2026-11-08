"""Pipeline runner and CLI entrypoint.

Executes the full promo discovery pipeline:
Parse -> Propose -> Validate -> Judge & Rank -> Export.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

from src.baseline import find_baseline_promos
from src.judge import judge_single_candidate, rank_survivors
from src.llm import get_usage_summary
from src.parser import format_timestamp, parse_all_episodes, parse_episode_file
from src.propose import propose_candidates
from src.validate import validate_candidates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run")


def process_single_episode(
    ep_data: Dict[str, Any],
    provider: str = "mock",
    model: str = None,
    judge_provider: str = None,
    judge_model: str = None,
    use_baseline: bool = False,
) -> Dict[str, Any]:
    """Process an episode through propose -> validate -> judge."""
    ep_num = ep_data["episode"]
    beats = ep_data["beats"]
    logger.info(f"Processing Episode {ep_num} ({len(beats)} beats)...")

    if use_baseline:
        candidates = find_baseline_promos(ep_data)
        validated = candidates
        evaluated = []
        for c in validated:
            c["verdict"] = "PASS"
            c["composite_score"] = 7.5
            evaluated.append(c)
    else:
        # 1. Propose
        raw_candidates = propose_candidates(ep_data, provider=provider, model=model)
        logger.info(f"  Proposed {len(raw_candidates)} raw candidate ranges.")

        # 2. Validate & Repair
        validated = validate_candidates(raw_candidates, beats)
        logger.info(f"  Validated {len(validated)} candidates after repair and deduplication.")

        # 3. Cold Judge
        evaluated = []
        for cand in validated:
            judged = judge_single_candidate(
                cand,
                beats,
                provider=judge_provider or provider,
                model=judge_model,
            )
            evaluated.append(judged)

    return {
        "episode": ep_num,
        "logline": ep_data.get("logline", ""),
        "total_beats": len(beats),
        "candidates": evaluated,
    }


def generate_markdown_summary(episodes_output: List[Dict[str, Any]]) -> str:
    """Format full unedited promos across all episodes into clean Markdown."""
    lines = [
        "# Kuku Microdrama Promo Discovery — All Episodes Summary",
        "",
        "| Ep | Start - End | Dur | Verdict | Score | Hook (First 3s) | Cliffhanger Cut | Why it Works |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for ep in episodes_output:
        for c in ep.get("candidates", []):
            ep_num = ep["episode"]
            timing = f"`{c['start_formatted']} - {c['end_formatted']}`"
            dur = f"{c['duration']:.1f}s"
            verdict = c.get("verdict", "PASS")
            score = f"{c.get('composite_score', 0.0):.1f}"
            hook = c.get("hook_text", "").replace("|", "-")[:45]
            cliff = c.get("cliffhanger_text", "").replace("|", "-")[:45]
            rationale = c.get("judge_rationale") or c.get("rationale") or ""
            rationale = rationale.replace("|", "-")[:65]

            lines.append(
                f"| E{ep_num:02d} | {timing} | {dur} | {verdict} | {score} | {hook}... | {cliff}... | {rationale}... |"
            )

    return "\n".join(lines)


def generate_ranked_markdown(ranked_promos: List[Dict[str, Any]]) -> str:
    """Format top 10-15 global promos into clean outputs/ranked.md."""
    lines = [
        "# Kuku Microdrama — Top Ranked Promotional Clips",
        "",
        "These top promos are ranked for maximum TikTok / Instagram Reels user acquisition efficiency.",
        "Criteria: Immediate 3s scroll-stopping hook, unresolved emotional cliffhanger, and zero-lore standalone clarity.",
        "",
    ]

    for idx, p in enumerate(ranked_promos, 1):
        ep = p["episode"]
        lines.extend(
            [
                f"## #{idx}: Episode {ep:02d} (`{p['start_formatted']} - {p['end_formatted']}` | {p['duration']:.1f}s)",
                "",
                f"- **Composite Rating**: `{p.get('composite_score', 9.0):.1f} / 10.0` (Hook: {p.get('hook_score', 9.0)}, Cliffhanger: {p.get('cliffhanger_score', 9.0)}, Standalone: {p.get('standalone_score', 9.0)})",
                f"- **Hook Beat (`{p['hook_beat_id']}`)**: \"{p.get('hook_text', '')}\"",
                f"- **Cliffhanger Beat (`{p['cliffhanger_beat_id']}`)**: \"{p.get('cliffhanger_text', '')}\"",
                f"- **Why it Works**: {p.get('rank_rationale') or p.get('judge_rationale') or p.get('rationale', '')}",
                f"- **Posting Strategy & Spoilers**: {p.get('spoiler_note', 'Early series asset; post in initial campaign waves.')}",
            ]
        )
        if p.get("repairs"):
            repairs_str = "; ".join(p["repairs"])
            lines.append(f"- **Validation Repairs Applied**: `{repairs_str}`")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Find microdrama promotional clips across screenplays.")
    parser.add_argument(
        "--input",
        "-i",
        default="assets/I Married a Broken Soldier. He was a Duke",
        help="Directory containing episode screenplay txt files.",
    )
    parser.add_argument(
        "--provider",
        "-p",
        default=os.getenv("LLM_PROVIDER", "mock"),
        help="LLM provider: 'gemini', 'openai', 'anthropic', or 'mock'.",
    )
    parser.add_argument("--model", "-m", default=None, help="Specific model name.")
    parser.add_argument("--judge-provider", default=None, help="Provider for cold-viewer judge.")
    parser.add_argument("--judge-model", default=None, help="Model for cold-viewer judge.")
    parser.add_argument("--max-episodes", type=int, default=None, help="Limit number of episodes to process.")
    parser.add_argument("--baseline", action="store_true", help="Use regex heuristic baseline instead of LLM.")
    parser.add_argument("--output-dir", default="outputs", help="Output directory.")

    args = parser.parse_args()

    os.makedirs(os.path.join(args.output_dir, "raw"), exist_ok=True)

    logger.info(f"Parsing screenplays from: {args.input}")
    episodes = parse_all_episodes(args.input)
    if args.max_episodes:
        episodes = episodes[: args.max_episodes]

    logger.info(f"Loaded {len(episodes)} episodes.")

    all_episode_outputs = []
    all_survivors = []

    for ep in episodes:
        res = process_single_episode(
            ep,
            provider=args.provider,
            model=args.model,
            judge_provider=args.judge_provider,
            judge_model=args.judge_model,
            use_baseline=args.baseline,
        )
        all_episode_outputs.append(res)

        # Save single episode raw output
        ep_file = os.path.join(args.output_dir, "raw", f"episode_{ep['episode']:03d}.json")
        with open(ep_file, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)

        # Collect survivors for global ranking
        for c in res["candidates"]:
            if c.get("verdict") == "PASS":
                all_survivors.append(c)

    # Save combined raw json
    raw_combined_file = os.path.join(args.output_dir, "raw", "all_episodes_promos.json")
    with open(raw_combined_file, "w", encoding="utf-8") as f:
        json.dump(all_episode_outputs, f, indent=2)
    logger.info(f"Saved full raw JSON to {raw_combined_file}")

    # Save raw markdown summary
    summary_md = generate_markdown_summary(all_episode_outputs)
    raw_md_file = os.path.join(args.output_dir, "raw", "all_episodes_summary.md")
    with open(raw_md_file, "w", encoding="utf-8") as f:
        f.write(summary_md)
    logger.info(f"Saved full raw Markdown summary to {raw_md_file}")

    # Global listwise ranking of survivors
    logger.info(f"Ranking {len(all_survivors)} survivor candidates...")
    ranked = rank_survivors(
        all_survivors,
        provider=args.judge_provider or args.provider,
        model=args.judge_model or args.model,
    )

    # Take top 15
    top_ranked = ranked[:15]

    ranked_md = generate_ranked_markdown(top_ranked)
    ranked_file = os.path.join(args.output_dir, "ranked.md")
    with open(ranked_file, "w", encoding="utf-8") as f:
        f.write(ranked_md)
    logger.info(f"Saved top {len(top_ranked)} ranked promos to {ranked_file}")

    # Usage summary
    usage = get_usage_summary()
    logger.info(f"Pipeline finished! Token and cost usage: {usage}")


if __name__ == "__main__":
    main()
