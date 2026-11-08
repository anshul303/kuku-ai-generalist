"""Batch runner CLI / API tool for executing promo discovery across 1 to 50 episodes at once."""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

from src.judge import judge_batch_candidates, rank_survivors
from src.llm import get_usage_summary, reset_usage_summary
from src.parser import parse_all_episodes, parse_episode_text
from src.propose import propose_batch_candidates
from src.validate import validate_candidates

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("batch_runner")


def safe_paraphrase(text: str, max_words: int = 8) -> str:
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def run_batch_discovery(
    episodes: List[Dict[str, Any]],
    provider: str = "mock",
    model: str = "mock",
    api_key: str = "",
    base_url: str = "",
    no_cache: bool = False,
    batch_size_eps: int = 10,
    batch_size_judge: int = 30,
) -> Dict[str, Any]:
    start_time = time.time()
    reset_usage_summary()

    if no_cache:
        os.environ["BYPASS_CACHE"] = "true"

    if api_key:
        if provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "openai_compatible":
            os.environ["OPENAI_COMPATIBLE_API_KEY"] = api_key

    if base_url:
        os.environ["OPENAI_COMPATIBLE_BASE_URL"] = base_url

    num_eps = len(episodes)
    episodes_map = {e["episode"]: e for e in episodes}

    # 1. Propose & Validate in Batches (~10 episodes per call)
    propose_batches = [episodes[i : i + batch_size_eps] for i in range(0, num_eps, batch_size_eps)]
    episodes_candidates: Dict[int, List[Dict[str, Any]]] = {e["episode"]: [] for e in episodes}

    total_proposed = 0
    total_repaired = 0
    total_rejected = 0

    for b_idx, batch in enumerate(propose_batches, 1):
        try:
            batch_proposals = propose_batch_candidates(batch, provider=provider, model=model)
            for ep in batch:
                ep_num = ep["episode"]
                raw_cands = batch_proposals.get(ep_num, [])
                total_proposed += len(raw_cands)

                validated = validate_candidates(raw_cands, ep["beats"])
                for v in validated:
                    if v.get("repairs"):
                        total_repaired += 1
                    episodes_candidates[ep_num].append(v)
        except Exception as e:
            logger.error(f"Error in propose batch {b_idx}: {e}")

    # Flatten all candidates for judging
    all_validated = []
    for ep_num in sorted(episodes_candidates.keys()):
        for c in episodes_candidates[ep_num]:
            all_validated.append(c)

    # 2. Judge in Batches (~30 clips per call)
    all_judged = []
    judge_batches = [all_validated[i : i + batch_size_judge] for i in range(0, len(all_validated), batch_size_judge)]
    for j_idx, j_batch in enumerate(judge_batches, 1):
        try:
            judged = judge_batch_candidates(j_batch, episodes_map, provider=provider, model=model)
            all_judged.extend(judged)
        except Exception as e:
            logger.error(f"Error in judge batch {j_idx}: {e}")
            all_judged.extend(j_batch)

    # Re-group by episode
    episodes_candidates = {e["episode"]: [] for e in episodes}
    for c in all_judged:
        ep_num = c["episode"]
        if ep_num in episodes_candidates:
            episodes_candidates[ep_num].append(c)

    # Filter survivors
    survivors = [c for c in all_judged if c.get("verdict") == "PASS"]


    # 3. Listwise Rank
    ranked_top = []
    if survivors:
        try:
            ranked_top = rank_survivors(survivors, provider=provider, model=model)
        except Exception as e:
            logger.error(f"Error in listwise ranking: {e}")
            # Fallback to sorting by composite_score
            survivors.sort(key=lambda x: x.get("composite_score", 0.0), reverse=True)
            ranked_top = survivors[:15]
            for idx, c in enumerate(ranked_top, 1):
                c["rank"] = idx

    # If ranking didn't assign rank property, assign 1..N
    for idx, c in enumerate(ranked_top, 1):
        c.setdefault("rank", idx)
        c["hook_text_safe"] = safe_paraphrase(c.get("hook_text", ""))
        c["cliffhanger_text_safe"] = safe_paraphrase(c.get("cliffhanger_text", ""))

    runtime = round(time.time() - start_time, 2)
    usage = get_usage_summary()

    # Format output episodes with safe excerpts
    sanitized_episodes = []
    for ep in episodes:
        ep_num = ep["episode"]
        cands = episodes_candidates.get(ep_num, [])
        safe_cands = []
        for c in cands:
            c_copy = dict(c)
            c_copy["hook_text_safe"] = safe_paraphrase(c.get("hook_text", ""))
            c_copy["cliffhanger_text_safe"] = safe_paraphrase(c.get("cliffhanger_text", ""))
            safe_cands.append(c_copy)

        sanitized_episodes.append({
            "episode": ep_num,
            "logline": ep.get("logline", ""),
            "total_beats": len(ep["beats"]),
            "candidates": safe_cands,
        })

    return {
        "total_episodes": num_eps,
        "total_beats": sum(len(e["beats"]) for e in episodes),
        "provider": provider,
        "model": model,
        "runtime_seconds": runtime,
        "total_calls": usage.get("total_calls", 0),
        "prompt_tokens": usage.get("total_prompt_tokens", 0),
        "completion_tokens": usage.get("total_completion_tokens", 0),
        "estimated_paid_tier_equivalent_usd": usage.get("estimated_paid_tier_equivalent_usd", 0.0),
        "actual_free_tier_cost_usd": 0.0,
        "total_candidates": len(all_validated),
        "total_survivors": len(survivors),
        "top_ranked": ranked_top[:15],
        "episodes": sanitized_episodes,
    }


def main():
    if len(sys.argv) < 2:
        payload = json.loads(sys.stdin.read())
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            payload = json.load(f)

    source = payload.get("source", "preloaded")
    provider = payload.get("provider", "mock")
    model = payload.get("model", "gemini-3.5-flash-lite" if provider == "gemini" else "mock")
    api_key = payload.get("api_key", "")
    base_url = payload.get("base_url", "")
    no_cache = payload.get("no_cache", False)
    max_episodes = payload.get("max_episodes", None)

    episodes = []
    if source == "preloaded":
        assets_dir = "assets/I Married a Broken Soldier. He was a Duke"
        if not os.path.exists(assets_dir):
            assets_dir = "assets"
        episodes = parse_all_episodes(assets_dir)
        if max_episodes and isinstance(max_episodes, int):
            episodes = episodes[:max_episodes]
    elif source == "uploaded":
        files_data = payload.get("files", [])
        for f in files_data:
            content = f.get("content", "")
            fname = f.get("filename", "uploaded_script.txt")
            if content.strip():
                ep_data = parse_episode_text(content, filename=fname)
                episodes.append(ep_data)
        episodes.sort(key=lambda x: x["episode"])
        if max_episodes and isinstance(max_episodes, int):
            episodes = episodes[:max_episodes]
    elif source == "text":
        text = payload.get("text", "")
        if text.strip():
            ep_data = parse_episode_text(text, filename="custom_scene.txt")
            episodes = [ep_data]

    if not episodes:
        print(json.dumps({"error": "No valid screenplay episodes found to process."}, indent=2))
        sys.exit(1)

    result = run_batch_discovery(
        episodes,
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        no_cache=no_cache,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
