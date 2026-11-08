"""Single episode CLI / API runner for live interactive promo discovery."""

import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

from run import process_single_episode

from src.parser import parse_episode_text


def safe_paraphrase(text: str, max_words: int = 8) -> str:
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def main():
    if len(sys.argv) < 2:
        payload = json.loads(sys.stdin.read())
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            payload = json.load(f)

    text = payload.get("text", "")
    provider = payload.get("provider", "mock")
    model = payload.get("model", "mock")
    api_key = payload.get("api_key", "")
    base_url = payload.get("base_url", "")

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

    ep_data = parse_episode_text(text, filename="custom_script.txt")
    res = process_single_episode(ep_data, provider=provider, model=model)

    # Sanitize candidate excerpts for safe display
    for c in res.get("candidates", []):
        c["hook_text_safe"] = safe_paraphrase(c.get("hook_text", ""))
        c["cliffhanger_text_safe"] = safe_paraphrase(c.get("cliffhanger_text", ""))

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
