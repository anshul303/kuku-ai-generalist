"""LLM abstraction interface supporting Gemini, Anthropic, OpenAI, and Mock providers.

Tracks prompt tokens, completion tokens, call counts, and estimated cost.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("src.llm")
logging.basicConfig(level=logging.INFO)


class QuotaExceededError(Exception):
    """Raised when an API provider returns a 429 quota exhaustion error."""

    def __init__(self, message: str, retry_delay: str = "Unknown"):
        super().__init__(message)
        self.retry_delay = retry_delay


CACHE_DIR = os.getenv("LLM_CACHE_DIR", ".cache/llm_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _get_cache_key(prompt: str, provider: str, model: str, params: Optional[Dict[str, Any]] = None) -> str:
    serialized = f"{provider}:{model}:{json.dumps(params or {}, sort_keys=True)}:{prompt}"
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _load_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _save_cache(cache_key: str, data: Dict[str, Any]):
    path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Failed to write cache {cache_key}: {e}")


# Pricing estimates in USD per million tokens
PRICING_PER_MILLION = {
    "gemini": {"input": 0.075, "output": 0.30},
    "openai": {"input": 0.15, "output": 0.60},
    "anthropic": {"input": 0.80, "output": 4.00},
    "openai_compatible": {"input": 0.0, "output": 0.0},
    "openai-compatible": {"input": 0.0, "output": 0.0},
    "mock": {"input": 0.0, "output": 0.0},
}


@dataclass
class UsageStats:
    total_calls: int = 0
    cache_hits: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_estimated_cost_usd: float = 0.0
    calls_by_provider: Dict[str, int] = field(default_factory=dict)

    def log_call(self, provider: str, prompt_tokens: int, completion_tokens: int, cost: float):
        self.total_calls += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_estimated_cost_usd += cost
        self.calls_by_provider[provider] = self.calls_by_provider.get(provider, 0) + 1
        logger.info(
            f"[{provider.upper()}] Call #{self.total_calls}: "
            f"+{prompt_tokens} prompt / +{completion_tokens} completion tokens, "
            f"est. paid-tier equivalent ${cost:.5f} (Total: ${self.total_estimated_cost_usd:.4f}, Actual Free-Tier: $0.00)"
        )


GLOBAL_USAGE = UsageStats()


def get_usage_summary() -> Dict[str, Any]:
    return {
        "total_calls": GLOBAL_USAGE.total_calls,
        "cache_hits": GLOBAL_USAGE.cache_hits,
        "total_prompt_tokens": GLOBAL_USAGE.total_prompt_tokens,
        "total_completion_tokens": GLOBAL_USAGE.total_completion_tokens,
        "estimated_paid_tier_equivalent_usd": round(GLOBAL_USAGE.total_estimated_cost_usd, 5),
        "actual_free_tier_cost_usd": 0.0,
        "total_estimated_cost_usd": round(GLOBAL_USAGE.total_estimated_cost_usd, 5),
        "calls_by_provider": dict(GLOBAL_USAGE.calls_by_provider),
    }


def reset_usage_summary():
    global GLOBAL_USAGE
    GLOBAL_USAGE = UsageStats()


def estimate_tokens(text: str) -> int:
    """Rough estimation: ~4 chars per token for English."""
    return max(1, len(text) // 4)


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Robustly extract JSON object or array from markdown codeblocks or raw strings."""
    text = text.strip()

    # Look for ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()

    # If directly parseable
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass

    # Extract first { ... } or [ ... ]
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        try:
            return json.loads(match.group(1), strict=False)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to extract valid JSON from LLM response:\n{text[:300]}...")


def _mock_propose_response(prompt: str) -> Dict[str, Any]:
    """Generate realistic candidate beat ranges from the episode transcript in the prompt."""
    # Check if this is a batched multi-episode prompt
    matches = list(re.finditer(r"===\s*EPISODE\s*(\d+)", prompt))
    if len(matches) >= 2:
        episodes_output = []
        for i, m in enumerate(matches):
            ep_num = int(m.group(1))
            start_pos = m.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(prompt)
            chunk = prompt[start_pos:end_pos]

            beat_ids = re.findall(r"\[(E\d+-B\d+)\]", chunk)
            if not beat_ids:
                beat_ids = re.findall(r"(E\d+-B\d+)", chunk)
            if not beat_ids:
                beat_ids = [f"E{ep_num:02d}-B001", f"E{ep_num:02d}-B005", f"E{ep_num:02d}-B015", f"E{ep_num:02d}-B025"]

            n = len(beat_ids)
            cands = []
            # Candidate 1: Opening hook (beats 0 to ~10)
            end_idx_1 = min(n - 1, max(3, n // 3))
            cands.append({
                "start_beat_id": beat_ids[0],
                "end_beat_id": beat_ids[end_idx_1],
                "hook_beat_id": beat_ids[min(1, n - 1)],
                "cliffhanger_beat_id": beat_ids[end_idx_1],
                "rationale": "High-impact opening confrontation immediately establishes emotional stakes without prior context.",
            })
            # Candidate 2: Mid/Climax escalation
            if n > 8:
                start_idx_2 = max(0, n - max(4, n // 3))
                end_idx_2 = n - 1
                cands.append({
                    "start_beat_id": beat_ids[start_idx_2],
                    "end_beat_id": beat_ids[end_idx_2],
                    "hook_beat_id": beat_ids[start_idx_2],
                    "cliffhanger_beat_id": beat_ids[end_idx_2],
                    "rationale": "Climax escalation ending on an unresolved cliffhanger right before the cut.",
                })
            episodes_output.append({"episode": ep_num, "candidates": cands})
        return {"episodes": episodes_output}



    # Otherwise, single episode prompt
    beat_ids = re.findall(r"\[(E\d+-B\d+)\]", prompt)
    if not beat_ids:
        # Fallback if pattern is slightly different
        beat_ids = re.findall(r"(E\d+-B\d+)", prompt)

    if not beat_ids:
        beat_ids = ["E01-B001", "E01-B005", "E01-B012", "E01-B020", "E01-B030"]

    n = len(beat_ids)
    candidates = []

    # Candidate 1: Opening hook (beats 0 to ~10)
    end_idx_1 = min(n - 1, max(3, n // 4))
    candidates.append(
        {
            "start_beat_id": beat_ids[0],
            "end_beat_id": beat_ids[end_idx_1],
            "hook_beat_id": beat_ids[min(1, n - 1)],
            "cliffhanger_beat_id": beat_ids[end_idx_1],
            "rationale": "High-impact opening confrontation immediately establishes the emotional stakes with no prior context required.",
        }
    )


    # Candidate 2: Mid-episode escalation
    if n > 12:
        start_idx_2 = n // 3
        end_idx_2 = min(n - 1, start_idx_2 + max(4, n // 5))
        candidates.append(
            {
                "start_beat_id": beat_ids[start_idx_2],
                "end_beat_id": beat_ids[end_idx_2],
                "hook_beat_id": beat_ids[start_idx_2],
                "cliffhanger_beat_id": beat_ids[end_idx_2],
                "rationale": "Pivotal dramatic shift where a public insult turns into an explosive confrontation.",
            }
        )

    # Candidate 3: Climax cliffhanger ending
    if n > 8:
        start_idx_3 = max(0, n - max(5, n // 3))
        end_idx_3 = n - 1
        candidates.append(
            {
                "start_beat_id": beat_ids[start_idx_3],
                "end_beat_id": beat_ids[end_idx_3],
                "hook_beat_id": beat_ids[start_idx_3],
                "cliffhanger_beat_id": beat_ids[end_idx_3],
                "rationale": "Episode climax building directly to the final unresolved revelation before cut to black.",
            }
        )

    return {"candidates": candidates}


def _mock_judge_response(prompt: str) -> Dict[str, Any]:
    """Generate mock cold-viewer evaluation and listwise ranking."""
    prompt_lower = prompt.lower()

    # Case 1: Batch candidate judging (asking for 'evaluations')
    if "evaluations" in prompt_lower or "candidate clip [id:" in prompt_lower:
        clip_ids = re.findall(r"\[ID:\s*([^\]]+)\]", prompt)
        if not clip_ids:
            clip_ids = re.findall(r"C\d+_\d+", prompt)
        evals = []
        for i, cid in enumerate(clip_ids):
            # Give realistic passing and varied scores
            h_s = round(8.5 + ((i * 3) % 10) * 0.1, 1)
            c_s = round(8.4 + ((i * 7) % 10) * 0.1, 1)
            s_s = round(8.2 + ((i * 5) % 10) * 0.1, 1)
            evals.append(
                {
                    "clip_id": cid,
                    "verdict": "PASS",
                    "hook_passed": True,
                    "cliffhanger_passed": True,
                    "standalone_passed": True,
                    "hook_score": min(9.8, h_s),
                    "cliffhanger_score": min(9.8, c_s),
                    "standalone_score": min(9.5, s_s),
                    "rationale": "High-tension melodramatic conflict stops feeds cold with an unresolved cliffhanger.",
                    "spoiler_note": "Safe for initial ad campaigns.",
                }
            )
        return {"evaluations": evals}

    # Case 2: Listwise ranking of passing survivors
    if "rank" in prompt_lower or "survivors" in prompt_lower:
        clip_ids = re.findall(r"Candidate\s*#?(\d+)", prompt, re.IGNORECASE)
        if not clip_ids:
            clip_ids = [str(i) for i in range(1, 16)]

        ranked_list = []
        for i, cid in enumerate(clip_ids[:15]):
            score = round(9.2 - (i * 0.15), 2)
            ranked_list.append(
                {
                    "candidate_id": int(cid),
                    "rank": i + 1,
                    "composite_score": score,
                    "hook_rating": round(min(10.0, score + 0.2), 1),
                    "cliffhanger_rating": round(min(10.0, score - 0.1), 1),
                    "standalone_rating": round(score, 1),
                    "verdict": "PASS" if score >= 7.0 else "FAIL",
                    "hook_analysis": "Opens with an immediate punchy visual/dialogue hook in the first 3s.",
                    "cliffhanger_analysis": "Leaves viewer suspended on high emotional tension right before resolution.",
                    "standalone_coherence": "Completely self-evident conflict; clear villain and victim.",
                    "rationale": f"High converting short-form ad segment with {score}/10 estimated conversion potential.",
                    "spoiler_note": "Low spoiler risk; introduces core premise.",
                }
            )
        return {"rankings": ranked_list}

    # Case 3: Single clip judge fallback
    return {
        "verdict": "PASS",
        "hook_passed": True,
        "cliffhanger_passed": True,
        "standalone_passed": True,
        "hook_score": 9.0,
        "cliffhanger_score": 8.8,
        "standalone_score": 9.2,
        "rationale": "Strong opening hook, intense cliffhanger, and crystal-clear melodrama dynamics.",
        "spoiler_note": "Safe for initial ad campaigns.",
    }



def _call_gemini(
    prompt: str, schema: Optional[Dict[str, Any]] = None, model: str = "gemini-3.5-flash"
) -> Dict[str, Any]:
    """Call Google Gemini API using direct REST requests with retry and backoff."""
    import time
    import requests

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    clean_model = model.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
        },
    }

    resp = None
    data = None
    text = ""
    parsed = None

    for attempt in range(4):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning(f"Gemini returned 0 candidates on attempt {attempt+1}. Retrying...")
                    time.sleep(2)
                    continue
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                try:
                    parsed = extract_json_from_text(text)
                    break
                except ValueError as json_err:
                    logger.warning(f"Malformed JSON from Gemini on attempt {attempt+1}: {json_err}. Retrying in 2s...")
                    time.sleep(2)
                    continue
            elif resp.status_code == 429:
                # Quota exceeded: Stop immediately and extract retry info
                err_data = resp.json().get("error", {})
                err_msg = err_data.get("message", "Quota limit reached")
                retry_match = re.search(r"Please retry in ([^\.]+)", err_msg)
                retry_time = retry_match.group(1).strip() if retry_match else "unknown duration"
                logger.error(f"Gemini API Quota Exceeded (429). Retry time: {retry_time}. Message: {err_msg[:200]}")
                raise QuotaExceededError(f"Gemini API Quota Exceeded (429): {err_msg}", retry_delay=retry_time)
            elif resp.status_code == 503:
                # Temporary high demand: short backoff
                wait_sec = 2**attempt + 2
                logger.warning(f"Gemini 503 high demand spike on attempt {attempt+1}. Retrying in {wait_sec}s...")
                time.sleep(wait_sec)
            else:
                raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text[:300]}")
        except requests.exceptions.RequestException as e:
            if attempt == 3:
                raise
            time.sleep(2**attempt + 2)
    else:
        err_msg = resp.text[:300] if resp is not None else "No response"
        raise RuntimeError(f"Gemini API request failed after retries: {err_msg}")

    if parsed is None:
        raise ValueError(f"Failed to obtain valid JSON from Gemini after 4 attempts. Last raw text:\n{text[:300]}...")

    # Normalize if LLM returns a top-level list
    if isinstance(parsed, list):
        if schema and "rankings" in schema.get("properties", {}):
            parsed = {"rankings": parsed}
        else:
            parsed = {"candidates": parsed}

    # Real token tracking directly from Google API metadata
    usage_meta = data.get("usageMetadata", {})
    prompt_tokens = usage_meta.get("promptTokenCount", estimate_tokens(prompt))
    completion_tokens = usage_meta.get("candidatesTokenCount", estimate_tokens(text))

    cost = (prompt_tokens * PRICING_PER_MILLION["gemini"]["input"] / 1_000_000) + (
        completion_tokens * PRICING_PER_MILLION["gemini"]["output"] / 1_000_000
    )
    GLOBAL_USAGE.log_call("gemini", prompt_tokens, completion_tokens, cost)
    model_version = data.get("modelVersion", clean_model)
    parsed["_metadata"] = {
        "provider": "gemini",
        "model_requested": clean_model,
        "api_model_version": model_version,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_paid_tier_equivalent_usd": cost,
        "actual_free_tier_cost_usd": 0.0,
        "cost_usd": cost,
    }
    return parsed


def _call_openai(
    prompt: str, schema: Optional[Dict[str, Any]] = None, model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """Call OpenAI API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": "You are an expert short-form microdrama editor and ad strategist. Always respond in valid JSON format."},
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    text = response.choices[0].message.content or "{}"
    parsed = extract_json_from_text(text)
    if isinstance(parsed, list):
        parsed = {"candidates": parsed}

    prompt_tokens = response.usage.prompt_tokens if response.usage else estimate_tokens(prompt)
    completion_tokens = response.usage.completion_tokens if response.usage else estimate_tokens(text)
    cost = (prompt_tokens * PRICING_PER_MILLION["openai"]["input"] / 1_000_000) + (
        completion_tokens * PRICING_PER_MILLION["openai"]["output"] / 1_000_000
    )
    GLOBAL_USAGE.log_call("openai", prompt_tokens, completion_tokens, cost)
    parsed["_metadata"] = {
        "provider": "openai",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost,
    }
    return parsed


def _call_anthropic(
    prompt: str, schema: Optional[Dict[str, Any]] = None, model: str = "claude-3-5-haiku-latest"
) -> Dict[str, Any]:
    """Call Anthropic Claude API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    system_prompt = (
        "You are an expert short-form microdrama editor and ad strategist. "
        "Always respond with a valid JSON markdown block containing the requested object."
    )

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.2,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text if response.content else "{}"
    parsed = extract_json_from_text(text)
    if isinstance(parsed, list):
        parsed = {"candidates": parsed}

    prompt_tokens = response.usage.input_tokens if hasattr(response, "usage") else estimate_tokens(prompt)
    completion_tokens = response.usage.output_tokens if hasattr(response, "usage") else estimate_tokens(text)
    cost = (prompt_tokens * PRICING_PER_MILLION["anthropic"]["input"] / 1_000_000) + (
        completion_tokens * PRICING_PER_MILLION["anthropic"]["output"] / 1_000_000
    )
    GLOBAL_USAGE.log_call("anthropic", prompt_tokens, completion_tokens, cost)
    parsed["_metadata"] = {
        "provider": "anthropic",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost,
    }
    return parsed


def _call_openai_compatible(
    prompt: str,
    schema: Optional[Dict[str, Any]] = None,
    model: str = "default",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Call any OpenAI-compatible API endpoint (Ollama, Together, Groq, vLLM, DeepSeek, LocalAI, etc.)."""
    import requests

    base = base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL") or os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
    resolved_model = model if model and model != "default" else (os.getenv("OPENAI_COMPATIBLE_MODEL") or "llama3")

    url = f"{base.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    system_msg = (
        "You are an expert short-form microdrama editor and ad strategist. "
        "Always respond strictly with a valid JSON object matching the requested schema."
    )
    payload: Dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    try:
        resp = requests.post(
            url,
            headers=headers,
            json={**payload, "response_format": {"type": "json_object"}},
            timeout=120,
        )
        if resp.status_code != 200:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
    except Exception as e:
        raise RuntimeError(f"Failed to connect to OpenAI-compatible provider at {url}: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI-compatible provider error ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError(f"OpenAI-compatible endpoint returned 0 choices: {data}")

    text = choices[0].get("message", {}).get("content", "") or "{}"
    parsed = extract_json_from_text(text)
    if isinstance(parsed, list):
        if schema and "rankings" in schema.get("properties", {}):
            parsed = {"rankings": parsed}
        else:
            parsed = {"candidates": parsed}

    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", estimate_tokens(prompt))
    completion_tokens = usage.get("completion_tokens", estimate_tokens(text))
    cost = 0.0

    GLOBAL_USAGE.log_call("openai_compatible", prompt_tokens, completion_tokens, cost)
    parsed["_metadata"] = {
        "provider": "openai_compatible",
        "model": resolved_model,
        "base_url": base,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost,
    }
    return parsed


def complete_json(
    prompt: str,
    schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    bypass_cache: bool = False,
) -> Dict[str, Any]:
    """Main JSON completion interface supporting all providers with fallback and logging."""
    if not provider:
        provider = os.getenv("LLM_PROVIDER")

    if not provider:
        # Auto-detect from available environment keys
        if os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            provider = "mock"

    provider = provider.lower().strip()
    resolved_model = model or ("gemini-3.5-flash-lite" if provider == "gemini" else ("gpt-4o-mini" if provider == "openai" else ("claude-3-5-haiku-latest" if provider == "anthropic" else "mock-rule-engine")))

    # Check disk cache
    cache_key = _get_cache_key(prompt, provider, resolved_model, schema)
    should_bypass = bypass_cache or (os.getenv("BYPASS_CACHE", "").lower() in ("true", "1", "yes"))
    if not should_bypass:
        cached_res = _load_cache(cache_key)
        if cached_res is not None:
            GLOBAL_USAGE.cache_hits += 1
            logger.info(f"[CACHE HIT] Key {cache_key[:12]}... (0 API calls, $0.00 cost)")
            cached_copy = json.loads(json.dumps(cached_res))
            cached_copy.setdefault("_metadata", {})
            cached_copy["_metadata"]["cached"] = True
            return cached_copy

    if provider == "mock":
        p_tok = estimate_tokens(prompt)
        schema_props = schema.get("properties", {}) if schema else {}
        prompt_head = prompt[:500].lower()

        if "promotional editor" in prompt_head or "propose" in prompt_head or "candidates" in schema_props:
            res = _mock_propose_response(prompt)
        elif "evaluations" in schema_props or "video ads judge" in prompt_head or "evaluation gates" in prompt_head:
            res = _mock_judge_response(prompt)
        elif "rankings" in schema_props or "listwise" in prompt_head or "rank the following" in prompt_head:
            res = _mock_judge_response(prompt)
        elif "verdict" in schema_props:
            res = _mock_judge_response(prompt)
        else:
            res = _mock_propose_response(prompt)

        c_tok = estimate_tokens(json.dumps(res))
        GLOBAL_USAGE.log_call("mock", p_tok, c_tok, 0.0)
        res["_metadata"] = {
            "provider": "mock",
            "model": "mock-rule-engine",
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "cost_usd": 0.0,
            "cached": False,
        }
        _save_cache(cache_key, res)
        return res

    if provider == "gemini":
        result = _call_gemini(prompt, schema=schema, model=resolved_model)
    elif provider == "openai":
        result = _call_openai(prompt, schema=schema, model=resolved_model)
    elif provider == "anthropic":
        result = _call_anthropic(prompt, schema=schema, model=resolved_model)
    elif provider in ("openai_compatible", "openai-compatible", "local"):
        result = _call_openai_compatible(prompt, schema=schema, model=resolved_model)
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. Choose from gemini, openai, anthropic, openai_compatible, mock."
        )

    result.setdefault("_metadata", {})
    result["_metadata"]["cached"] = False
    _save_cache(cache_key, result)
    return result
