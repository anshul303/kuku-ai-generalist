"""LLM abstraction interface supporting Gemini, Anthropic, OpenAI, and Mock providers.

Tracks prompt tokens, completion tokens, call counts, and estimated cost.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("src.llm")
logging.basicConfig(level=logging.INFO)


# Pricing estimates in USD per million tokens
PRICING_PER_MILLION = {
    "gemini": {"input": 0.075, "output": 0.30},
    "openai": {"input": 0.15, "output": 0.60},
    "anthropic": {"input": 0.80, "output": 4.00},
    "mock": {"input": 0.0, "output": 0.0},
}


@dataclass
class UsageStats:
    total_calls: int = 0
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
            f"est. cost ${cost:.5f} (Total cost: ${self.total_estimated_cost_usd:.4f})"
        )


GLOBAL_USAGE = UsageStats()


def get_usage_summary() -> Dict[str, Any]:
    return {
        "total_calls": GLOBAL_USAGE.total_calls,
        "total_prompt_tokens": GLOBAL_USAGE.total_prompt_tokens,
        "total_completion_tokens": GLOBAL_USAGE.total_completion_tokens,
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
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract first { ... } or [ ... ]
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to extract valid JSON from LLM response:\n{text[:300]}...")


def _mock_propose_response(prompt: str) -> Dict[str, Any]:
    """Generate realistic candidate beat ranges from the episode transcript in the prompt."""
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
    # Check if prompt is a listwise ranking prompt or single clip judge
    if "rank" in prompt.lower() or "survivors" in prompt.lower() or "candidates" in prompt.lower():
        # Listwise ranking
        clip_ids = re.findall(r"Candidate\s*#?(\d+)", prompt, re.IGNORECASE)
        if not clip_ids:
            clip_ids = ["1", "2", "3"]

        ranked_list = []
        for i, cid in enumerate(clip_ids):
            score = round(9.5 - (i * 0.4), 2)
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
    else:
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
    prompt: str, schema: Optional[Dict[str, Any]] = None, model: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """Call Google Gemini API using google-genai SDK or REST."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )
    if schema:
        config.response_schema = schema

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    text = response.text or ""
    parsed = extract_json_from_text(text)

    # Track usage if metadata available
    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(text)
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", prompt_tokens)
        completion_tokens = getattr(response.usage_metadata, "candidates_token_count", completion_tokens)

    cost = (prompt_tokens * PRICING_PER_MILLION["gemini"]["input"] / 1_000_000) + (
        completion_tokens * PRICING_PER_MILLION["gemini"]["output"] / 1_000_000
    )
    GLOBAL_USAGE.log_call("gemini", prompt_tokens, completion_tokens, cost)
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

    prompt_tokens = response.usage.prompt_tokens if response.usage else estimate_tokens(prompt)
    completion_tokens = response.usage.completion_tokens if response.usage else estimate_tokens(text)
    cost = (prompt_tokens * PRICING_PER_MILLION["openai"]["input"] / 1_000_000) + (
        completion_tokens * PRICING_PER_MILLION["openai"]["output"] / 1_000_000
    )
    GLOBAL_USAGE.log_call("openai", prompt_tokens, completion_tokens, cost)
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

    prompt_tokens = response.usage.input_tokens if hasattr(response, "usage") else estimate_tokens(prompt)
    completion_tokens = response.usage.output_tokens if hasattr(response, "usage") else estimate_tokens(text)
    cost = (prompt_tokens * PRICING_PER_MILLION["anthropic"]["input"] / 1_000_000) + (
        completion_tokens * PRICING_PER_MILLION["anthropic"]["output"] / 1_000_000
    )
    GLOBAL_USAGE.log_call("anthropic", prompt_tokens, completion_tokens, cost)
    return parsed


def complete_json(
    prompt: str,
    schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
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

    if provider == "mock":
        p_tok = estimate_tokens(prompt)
        # Check task based on schema or prompt structure
        schema_props = schema.get("properties", {}) if schema else {}
        if "candidates" in schema_props:
            res = _mock_propose_response(prompt)
        elif "rankings" in schema_props:
            res = _mock_judge_response(prompt)
        elif "verdict" in schema_props:
            res = _mock_judge_response(prompt)
        elif "rank" in prompt.lower() and "survivor" in prompt.lower():
            res = _mock_judge_response(prompt)
        elif "ruthless" in prompt.lower() or "evaluation gates" in prompt.lower():
            res = _mock_judge_response(prompt)
        else:
            res = _mock_propose_response(prompt)
        c_tok = estimate_tokens(json.dumps(res))
        GLOBAL_USAGE.log_call("mock", p_tok, c_tok, 0.0)
        return res

    try:
        if provider == "gemini":
            return _call_gemini(prompt, schema=schema, model=model or "gemini-2.5-flash")
        elif provider == "openai":
            return _call_openai(prompt, schema=schema, model=model or "gpt-4o-mini")
        elif provider == "anthropic":
            return _call_anthropic(prompt, schema=schema, model=model or "claude-3-5-haiku-latest")
        else:
            raise ValueError(f"Unknown provider '{provider}'. Choose from gemini, openai, anthropic, mock.")
    except Exception as e:
        logger.warning(f"Provider '{provider}' call failed ({e}). Falling back to mock provider.")
        p_tok = estimate_tokens(prompt)
        schema_props = schema.get("properties", {}) if schema else {}
        if "candidates" in schema_props:
            res = _mock_propose_response(prompt)
        elif "rankings" in schema_props or "verdict" in schema_props:
            res = _mock_judge_response(prompt)
        elif "ruthless" in prompt.lower() or "evaluation gates" in prompt.lower():
            res = _mock_judge_response(prompt)
        else:
            res = _mock_propose_response(prompt)
        c_tok = estimate_tokens(json.dumps(res))
        GLOBAL_USAGE.log_call("mock_fallback", p_tok, c_tok, 0.0)
        return res
