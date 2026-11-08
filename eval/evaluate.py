"""Evaluation suite: computes Top-3 Hit Rate for Baseline vs. Pipeline Run 1 and Run 2.

Evaluates against hand-curated ground truth in eval/ground_truth_user.json.
Enforces a strict >= 50% temporal IoU threshold.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import sys
from typing import Any, Dict, List, Tuple

from src.baseline import find_baseline_promos
from src.parser import parse_episode_file
from src.validate import compute_interval_overlap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eval")

IOU_HIT_THRESHOLD = 0.50  # Strict >= 50% temporal overlap threshold


def load_ground_truth(filepath: str = "eval/ground_truth_user.json") -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Ground truth file '{filepath}' not found. "
            "Please supply user-authored ground truth promos in eval/ground_truth_user.json."
        )
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_hit_rate(
    candidates: List[Dict[str, Any]], gold_promos: List[Dict[str, Any]], top_k: int = 3
) -> Tuple[bool, float, Dict[str, Any]]:
    """Determine if any of the top_k candidates overlaps with any gold promo above threshold."""
    top_candidates = candidates[:top_k]
    best_iou = 0.0
    matched_gold = None
    matched_cand = None

    for cand in top_candidates:
        c_start = cand["start_time"]
        c_end = cand["end_time"]
        for gold in gold_promos:
            g_start = gold["start_time"]
            g_end = gold["end_time"]
            iou = compute_interval_overlap(c_start, c_end, g_start, g_end)
            if iou > best_iou:
                best_iou = iou
                matched_gold = gold
                matched_cand = cand

    hit = best_iou >= IOU_HIT_THRESHOLD
    match_info = {
        "hit": hit,
        "best_iou": round(best_iou, 3),
        "matched_cand_range": (
            f"{matched_cand['start_formatted']} - {matched_cand['end_formatted']}" if matched_cand else "None"
        ),
        "matched_gold_desc": matched_gold.get("hook_description", "None") if matched_gold else "None",
    }
    return hit, best_iou, match_info


def load_run_candidates(ep_num: int, raw_dir: str) -> List[Dict[str, Any]]:
    """Load candidates from an unedited episode JSON output."""
    raw_file = os.path.join(raw_dir, f"episode_{ep_num:03d}.json")
    if os.path.exists(raw_file):
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                ep_json = json.load(f)
                return ep_json.get("candidates", [])
        except Exception as e:
            logger.warning(f"Could not read {raw_file}: {e}")
    return []


def run_evaluation(
    data_dir: str = "assets/I Married a Broken Soldier. He was a Duke",
    gt_file: str = "eval/ground_truth_user.json",
    run1_dir: str = "outputs/raw_real_run1/raw",
    run2_dir: str = "outputs/raw_real_run2/raw",
) -> Dict[str, Any]:
    gt_list = load_ground_truth(gt_file)
    gt_map = {item["episode"]: item["promos"] for item in gt_list}
    episode_list = sorted(gt_map.keys())
    total_episodes = len(episode_list)

    baseline_hits = 0
    run1_hits = 0
    run2_hits = 0
    comparison_rows = []

    for ep_num in episode_list:
        matches = glob.glob(os.path.join(data_dir, f"episode-{ep_num:03d}*.txt"))
        if not matches:
            logger.warning(f"Screenplay file for episode {ep_num} not found.")
            continue
        ep_file = matches[0]

        ep_data = parse_episode_file(ep_file)
        golds = gt_map[ep_num]

        # 1. Baseline
        base_cands = find_baseline_promos(ep_data, max_promos=3)
        b_hit, b_iou, _ = calculate_hit_rate(base_cands, golds, top_k=3)
        if b_hit:
            baseline_hits += 1

        # 2. Pipeline Run 1
        r1_cands = load_run_candidates(ep_num, run1_dir)
        r1_hit, r1_iou, _ = calculate_hit_rate(r1_cands, golds, top_k=3)
        if r1_hit:
            run1_hits += 1

        # 3. Pipeline Run 2
        r2_cands = load_run_candidates(ep_num, run2_dir)
        r2_hit, r2_iou, _ = calculate_hit_rate(r2_cands, golds, top_k=3)
        if r2_hit:
            run2_hits += 1

        comparison_rows.append(
            {
                "episode": ep_num,
                "baseline_hit": b_hit,
                "baseline_best_iou": b_iou,
                "run1_hit": r1_hit,
                "run1_best_iou": r1_iou,
                "run2_hit": r2_hit,
                "run2_best_iou": r2_iou,
            }
        )

    results = {
        "n": total_episodes,
        "episodes": episode_list,
        "baseline_top3_hit_rate": round(baseline_hits / max(1, total_episodes), 3),
        "run1_top3_hit_rate": round(run1_hits / max(1, total_episodes), 3),
        "run2_top3_hit_rate": round(run2_hits / max(1, total_episodes), 3),
        "per_episode_results": comparison_rows,
    }
    return results


def main():
    gt_file = sys.argv[1] if len(sys.argv) > 1 else "eval/ground_truth_user.json"
    if not os.path.exists(gt_file):
        print(f"Ground truth file '{gt_file}' not found. Awaiting user-authored ground truth.")
        sys.exit(1)

    results = run_evaluation(gt_file=gt_file)
    n = results["n"]

    print("\n" + "=" * 70)
    print("📊 BENCHMARK EVALUATION RESULTS (Strict >= 50% IoU)")
    print(f"Sample Size (n):              {n} Episodes")
    print(f"Episodes Evaluated:           {results['episodes']}")
    print(f"Heuristic Baseline Hit Rate:  {results['baseline_top3_hit_rate'] * 100:.1f}% ({int(results['baseline_top3_hit_rate'] * n)}/{n})")
    print(f"Pipeline Run 1 Hit Rate:      {results['run1_top3_hit_rate'] * 100:.1f}% ({int(results['run1_top3_hit_rate'] * n)}/{n})")
    print(f"Pipeline Run 2 Hit Rate:      {results['run2_top3_hit_rate'] * 100:.1f}% ({int(results['run2_top3_hit_rate'] * n)}/{n})")
    print("=" * 70)
    print("\nPer-Episode Breakdown:")
    print("| Ep | Baseline Hit | Base IoU | Run 1 Hit | Run 1 IoU | Run 2 Hit | Run 2 IoU |")
    print("|---|---|---|---|---|---|---|")
    for r in results["per_episode_results"]:
        b_str = "✅ HIT " if r["baseline_hit"] else "❌ MISS"
        r1_str = "✅ HIT " if r["run1_hit"] else "❌ MISS"
        r2_str = "✅ HIT " if r["run2_hit"] else "❌ MISS"
        print(
            f"| E{r['episode']:02d} | {b_str}      | {r['baseline_best_iou']:.3f}    | "
            f"{r1_str}   | {r1_best_iou if (r1_best_iou := r['run1_best_iou']) else 0.0:.3f}     | "
            f"{r2_str}   | {r['run2_best_iou']:.3f}     |"
        )
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
