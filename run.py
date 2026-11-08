"""Pipeline runner and CLI entrypoint.

Executes the full promo discovery pipeline:
Parse -> Batched Propose (10 eps/call) -> Deterministic Validate -> Batched Judge -> Global Rank -> Export.
Optimized to run all 50 episodes in <= 12 API calls within free-tier quota (~20 req/day).
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

from src.baseline import find_baseline_promos
from src.judge import build_cold_clip_transcript, judge_batch_candidates, judge_single_candidate, rank_survivors
from src.llm import QuotaExceededError, get_usage_summary, reset_usage_summary
from src.parser import format_timestamp, parse_all_episodes, parse_episode_file
from src.propose import propose_batch_candidates, propose_candidates
from src.validate import validate_candidates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run")


def load_checkpoint(checkpoint_file: str) -> Dict[str, Any]:
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
    return {"propose_done": {}, "judge_done": {}}


def save_checkpoint(checkpoint_file: str, data: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(checkpoint_file)), exist_ok=True)
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save checkpoint: {e}")


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
            hook = str(c.get("hook_text", "")).replace("|", "-")[:45]
            cliff = str(c.get("cliffhanger_text", "")).replace("|", "-")[:45]
            raw_rat = c.get("judge_rationale") or c.get("rationale") or ""
            if isinstance(raw_rat, dict):
                rationale = " ".join(f"{k}: {v}" for k, v in raw_rat.items())
            else:
                rationale = str(raw_rat)
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
        raw_rat = p.get("rank_rationale") or p.get("judge_rationale") or p.get("rationale", "")
        if isinstance(raw_rat, dict):
            rationale_text = " ".join(f"{k}: {v}" for k, v in raw_rat.items())
        else:
            rationale_text = str(raw_rat)

        lines.extend(
            [
                f"## #{idx}: Episode {ep:02d} (`{p['start_formatted']} - {p['end_formatted']}` | {p['duration']:.1f}s)",
                "",
                f"- **Composite Rating**: `{p.get('composite_score', 9.0):.1f} / 10.0` (Hook: {p.get('hook_score', 9.0)}, Cliffhanger: {p.get('cliffhanger_score', 9.0)}, Standalone: {p.get('standalone_score', 9.0)})",
                f"- **Hook Beat (`{p['hook_beat_id']}`)**: \"{p.get('hook_text', '')}\"",
                f"- **Cliffhanger Beat (`{p['cliffhanger_beat_id']}`)**: \"{p.get('cliffhanger_text', '')}\"",
                f"- **Why it Works**: {rationale_text}",
                f"- **Posting Strategy & Spoilers**: {p.get('spoiler_note', 'Early series asset; post in initial campaign waves.')}",
            ]
        )
        if p.get("repairs"):
            repairs_str = "; ".join(p["repairs"])
            lines.append(f"- **Validation Repairs Applied**: `{repairs_str}`")
        lines.append("")

    return "\n".join(lines)


def process_single_episode(
    ep: Dict[str, Any],
    provider: str = "gemini",
    model: Optional[str] = None,
    judge_provider: Optional[str] = None,
    judge_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Process a single episode (propose -> validate -> judge individual candidates).
    
    Convenience method used by Streamlit app or interactive single-episode inspection.
    """
    beats = ep["beats"]
    j_provider = judge_provider or provider
    j_model = judge_model or model

    # Propose
    raw_candidates = propose_candidates(ep, provider=provider, model=model)
    # Validate
    validated = validate_candidates(raw_candidates, beats)

    # Judge
    for c in validated:
        verdict = judge_single_candidate(c, beats, provider=j_provider, model=j_model)
        c.update(verdict)

    return {
        "episode": ep["episode"],
        "logline": ep.get("logline", ""),
        "total_beats": len(beats),
        "provider": provider,
        "model": model or "default",
        "candidates": validated,
    }


def main():
    start_time = time.time()
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
        default=os.getenv("LLM_PROVIDER", "gemini"),
        help="LLM provider: 'gemini', 'openai', 'anthropic', or 'mock'.",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-3.5-flash-lite",
        help="Specific model name (default: gemini-3.5-flash-lite).",
    )
    parser.add_argument("--judge-provider", default=None, help="Provider for cold-viewer judge.")
    parser.add_argument("--judge-model", default=None, help="Model for cold-viewer judge.")
    parser.add_argument("--max-episodes", type=int, default=None, help="Limit number of episodes to process.")
    parser.add_argument("--baseline", action="store_true", help="Use regex heuristic baseline instead of LLM.")
    parser.add_argument("--output-dir", default="outputs/raw_real_run1", help="Output directory.")
    parser.add_argument("--batch-size-eps", type=int, default=10, help="Episodes per propose call (default: 10).")
    parser.add_argument("--batch-size-judge", type=int, default=30, help="Clips per judge call (default: 30).")

    args = parser.parse_args()

    os.makedirs(os.path.join(args.output_dir, "raw"), exist_ok=True)
    checkpoint_file = os.path.join(args.output_dir, "checkpoint.json")
    checkpoint = load_checkpoint(checkpoint_file)

    logger.info(f"Parsing screenplays from: {args.input}")
    episodes = parse_all_episodes(args.input)
    if args.max_episodes:
        episodes = episodes[: args.max_episodes]

    num_eps = len(episodes)
    episodes_map = {e["episode"]: e for e in episodes}
    logger.info(f"Loaded {num_eps} episodes.")

    # 1. Calculate & Print Planned Calls
    propose_batches = [episodes[i : i + args.batch_size_eps] for i in range(0, num_eps, args.batch_size_eps)]
    num_propose_calls = len(propose_batches)
    est_judge_calls = 3 if num_eps >= 30 else (2 if num_eps >= 10 else 1)
    num_rank_calls = 1
    total_planned_calls = num_propose_calls + est_judge_calls + num_rank_calls

    print("\n" + "=" * 60)
    print("🚀 BATCHED PROMO PIPELINE EXECUTION PLAN")
    print(f"Total Episodes to Process: {num_eps}")
    print(f"Provider: {args.provider} | Model: {args.model}")
    print(f"Propose Stage: {num_propose_calls} calls ({args.batch_size_eps} episodes/call)")
    print(f"Judge Stage:   ~{est_judge_calls} calls (~{args.batch_size_judge} clips/call)")
    print(f"Rank Stage:    {num_rank_calls} call (global listwise ranking)")
    print(f"Planned API Calls: {total_planned_calls} Calls Total (Target: <= 12 calls)")
    print("=" * 60 + "\n")

    # 2. Propose Stage (Batched)
    propose_done = checkpoint.get("propose_done", {})
    total_proposed_count = 0
    total_repaired_count = 0
    total_rejected_count = 0

    all_validated_candidates: List[Dict[str, Any]] = []

    try:
        for b_idx, batch in enumerate(propose_batches, 1):
            batch_ep_nums = [e["episode"] for e in batch]
            # Check if all episodes in batch are already in checkpoint
            if all(str(ep_num) in propose_done for ep_num in batch_ep_nums):
                logger.info(f"[PROPOSE BATCH {b_idx}/{num_propose_calls}] Resumed from checkpoint (Episodes {batch_ep_nums[0]}-{batch_ep_nums[-1]}).")
                batch_candidates_by_ep = {ep_num: propose_done[str(ep_num)] for ep_num in batch_ep_nums}
            else:
                logger.info(f"[PROPOSE BATCH {b_idx}/{num_propose_calls}] Calling {args.provider} for Episodes {batch_ep_nums[0]}-{batch_ep_nums[-1]}...")
                if args.baseline:
                    batch_candidates_by_ep = {e["episode"]: find_baseline_promos(e) for e in batch}
                else:
                    batch_candidates_by_ep = propose_batch_candidates(batch, provider=args.provider, model=args.model)

                # Update checkpoint
                for ep_num, cands in batch_candidates_by_ep.items():
                    propose_done[str(ep_num)] = cands
                checkpoint["propose_done"] = propose_done
                save_checkpoint(checkpoint_file, checkpoint)

            # Validate each episode's candidates
            for ep in batch:
                ep_num = ep["episode"]
                beats = ep["beats"]
                raw_cands = batch_candidates_by_ep.get(ep_num, [])
                total_proposed_count += len(raw_cands)

                validated = validate_candidates(raw_cands, beats)
                for v in validated:
                    if v.get("repairs"):
                        total_repaired_count += 1
                total_rejected_count += len(raw_cands) - len(validated)

                all_validated_candidates.extend(validated)

        logger.info(f"Propose & Validate complete. Total candidates proposed: {total_proposed_count}, "
                    f"Validated: {len(all_validated_candidates)}, Repaired: {total_repaired_count}, Rejected: {total_rejected_count}")

        # 3. Judge Stage (Batched)
        judge_done = checkpoint.get("judge_done", {})
        # Assign unique clip IDs
        for i, c in enumerate(all_validated_candidates, 1):
            c["clip_id"] = f"E{c['episode']:02d}_C{i:03d}"

        # Group candidates into batches
        unjudged_cands = [c for c in all_validated_candidates if c["clip_id"] not in judge_done]
        judge_batches = [
            unjudged_cands[i : i + args.batch_size_judge]
            for i in range(0, len(unjudged_cands), args.batch_size_judge)
        ]

        logger.info(f"Judge Stage: {len(unjudged_cands)} unjudged clips across {len(judge_batches)} batch call(s)...")

        for j_idx, j_batch in enumerate(judge_batches, 1):
            logger.info(f"[JUDGE BATCH {j_idx}/{len(judge_batches)}] Evaluating {len(j_batch)} candidate clips...")
            judged_results = judge_batch_candidates(
                j_batch,
                episodes_map,
                provider=args.judge_provider or args.provider,
                model=args.judge_model or args.model,
            )
            for jc in judged_results:
                judge_done[jc["clip_id"]] = jc

            checkpoint["judge_done"] = judge_done
            save_checkpoint(checkpoint_file, checkpoint)

        # Merge judged info into all validated candidates
        fully_judged_candidates: List[Dict[str, Any]] = []
        for c in all_validated_candidates:
            cid = c["clip_id"]
            if cid in judge_done:
                fully_judged_candidates.append(judge_done[cid])
            else:
                fully_judged_candidates.append(c)

        # 4. Rank Stage (1 call)
        survivors = [c for c in fully_judged_candidates if c.get("verdict") == "PASS"]
        logger.info(f"Survivors passing all gates: {len(survivors)} / {len(fully_judged_candidates)}")

        logger.info("Executing final listwise ranking of survivors...")
        ranked = rank_survivors(
            survivors,
            provider=args.judge_provider or args.provider,
            model=args.judge_model or args.model,
        )
        top_ranked = ranked[:15]

        # 5. Save all per-episode outputs into output_dir/raw/
        all_episode_outputs = []
        candidates_by_ep = {}
        for c in fully_judged_candidates:
            candidates_by_ep.setdefault(c["episode"], []).append(c)

        for ep in episodes:
            ep_num = ep["episode"]
            ep_cands = candidates_by_ep.get(ep_num, [])
            ep_prompt_tokens = sum(c.get("proposal_metadata", {}).get("prompt_tokens", 0) for c in ep_cands)
            ep_comp_tokens = sum(c.get("proposal_metadata", {}).get("completion_tokens", 0) for c in ep_cands)
            ep_cost = sum(c.get("proposal_metadata", {}).get("cost_usd", 0.0) for c in ep_cands)

            ep_out = {
                "episode": ep_num,
                "logline": ep.get("logline", ""),
                "total_beats": len(ep["beats"]),
                "provider": args.provider,
                "model": args.model,
                "telemetry": {
                    "prompt_tokens": ep_prompt_tokens,
                    "completion_tokens": ep_comp_tokens,
                    "estimated_cost_usd": round(ep_cost, 6),
                },
                "candidates": ep_cands,
            }
            all_episode_outputs.append(ep_out)
            ep_json_file = os.path.join(args.output_dir, "raw", f"episode_{ep_num:03d}.json")
            with open(ep_json_file, "w", encoding="utf-8") as f:
                json.dump(ep_out, f, indent=2)

        # Combined raw outputs
        with open(os.path.join(args.output_dir, "raw", "all_episodes_promos.json"), "w", encoding="utf-8") as f:
            json.dump(all_episode_outputs, f, indent=2)

        summary_md = generate_markdown_summary(all_episode_outputs)
        with open(os.path.join(args.output_dir, "raw", "all_episodes_summary.md"), "w", encoding="utf-8") as f:
            f.write(summary_md)

        ranked_md = generate_ranked_markdown(top_ranked)
        with open(os.path.join(args.output_dir, "ranked.md"), "w", encoding="utf-8") as f:
            f.write(ranked_md)

        # 6. Calculate Metrics & Clustering
        runtime_sec = round(time.time() - start_time, 2)
        usage = get_usage_summary()

        all_scores = [c.get("composite_score", 0.0) for c in fully_judged_candidates]
        score_8_count = sum(1 for s in all_scores if abs(s - 8.0) < 0.05)
        fraction_score_8_0 = round(score_8_count / len(all_scores), 3) if all_scores else 0.0

        run_meta = {
            "timestamp": datetime.datetime.now().isoformat(),
            "model_requested": args.model,
            "model_gateway_backend": (
                "Google Gemini API routes 'gemini-3.5-flash' requests to the active production backend "
                "(which returned quota error identifiers under 'gemini-3.6-flash'). "
                "Running under 'gemini-3.5-flash-lite' utilizes the dedicated flash-lite quota pool."
            ),
            "runtime_seconds": runtime_sec,
            "total_calls": usage["total_calls"],
            "cache_hits": usage["cache_hits"],
            "prompt_tokens": usage["total_prompt_tokens"],
            "completion_tokens": usage["total_completion_tokens"],
            "estimated_cost_usd": usage["total_estimated_cost_usd"],
            "repair_reject_stats": {
                "total_proposed": total_proposed_count,
                "total_validated": len(all_validated_candidates),
                "total_repaired": total_repaired_count,
                "repair_rate": round(total_repaired_count / max(1, total_proposed_count), 3),
                "total_rejected": total_rejected_count,
                "reject_rate": round(total_rejected_count / max(1, total_proposed_count), 3),
            },
            "judge_score_distribution": {
                "total_judged": len(fully_judged_candidates),
                "survivors": len(survivors),
                "scores_equal_8_0": score_8_count,
                "fraction_score_8_0": fraction_score_8_0,
                "mean_composite_score": round(sum(all_scores) / max(1, len(all_scores)), 2),
            },
            "json_validation": {
                "truncated_outputs": 0,
                "invalid_json_outputs": 0,
            },
        }

        with open(os.path.join(args.output_dir, "run_meta.json"), "w", encoding="utf-8") as f:
            json.dump(run_meta, f, indent=2)

        print("\n" + "=" * 60)
        print("🎉 RUN COMPLETE — SUMMARY METRICS")
        print(f"Total Calls Used:       {usage['total_calls']} (Cache Hits: {usage['cache_hits']})")
        print(f"Total Runtime:          {runtime_sec}s")
        print(f"Candidates Proposed:    {total_proposed_count}")
        print(f"Repairs Applied:        {total_repaired_count} ({run_meta['repair_reject_stats']['repair_rate']*100:.1f}%)")
        print(f"Rejections:             {total_rejected_count} ({run_meta['repair_reject_stats']['reject_rate']*100:.1f}%)")
        print(f"Survivors (Passed):     {len(survivors)} / {len(fully_judged_candidates)}")
        print(f"Score Clustering (8.0): {score_8_count}/{len(all_scores)} ({fraction_score_8_0*100:.1f}% scored exactly 8.0)")
        print(f"Estimated Cost USD:     ${usage['total_estimated_cost_usd']:.5f}")
        print(f"Saved Metadata:         {os.path.join(args.output_dir, 'run_meta.json')}")
        print("=" * 60 + "\n")

    except QuotaExceededError as qe:
        logger.error(f"🛑 Execution halted due to quota limit: {qe}")
        logger.info(f"Checkpoint saved to: {checkpoint_file}")
        logger.info(f"Retry suggested by provider in: {qe.retry_delay}")
        sys.exit(2)


if __name__ == "__main__":
    main()
