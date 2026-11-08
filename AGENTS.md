# AGENTS.md — Agent & Developer Guide

This file provides system architecture, coding guidelines, invariants, and operational runbooks for AI agents and engineers working on the **Kuku Microdrama Promo Discovery Tool**.

---

## 1. Project Mission & Context

- **Objective**: Build an automated tool that parses vertical microdrama screenplays (1–2 min episodes) and discovers high-converting **20 to 60-second** promotional clips (ads) for TikTok, Instagram Reels, and YouTube Shorts.
- **Show Under Test**: *I Married a Broken Soldier. He was a Duke* (50 episodes, English, US audience).
- **Core Promo Criteria**:
  1. **Hook (0–3s)**: Stops scrolling viewers cold (slaps, public humiliation, shocking reveals, cruel insults).
  2. **Cliffhanger Cut**: Cuts at peak unresolved tension before resolution.
  3. **Standalone Coherence**: Makes immediate melodramatic sense to cold scrollers with zero prior lore.

---

## 2. Directory Structure

```text
kuku/
├── assets/                     # Confidential screenplays (GIT-IGNORED)
├── src/
│   ├── __init__.py
│   ├── parser.py               # Deterministic screenplay parser -> JSON beats & shots
│   ├── llm.py                  # Multi-provider LLM interface (gemini, openai, anthropic, mock)
│   ├── propose.py              # Candidate proposal engine (beat-ID ranges only)
│   ├── validate.py             # 20-60s duration repair, hook offset & boundary enforcement
│   ├── judge.py                # Cold-viewer judge & listwise ranking engine
│   └── baseline.py             # Heuristic regex baseline for evaluation comparison
├── eval/
│   ├── ground_truth.json       # Editor gold-standard clips for Episodes 1–10
│   ├── evaluate.py             # Hit rate, stability, and model agreement benchmark
│   └── failures.md             # 6 documented real failure modes and mitigations
├── outputs/
│   ├── raw/                    # Full unedited JSONs for all 50 episodes & summary markdown
│   └── ranked.md               # Top 15 global promo clips across the entire series
├── tests/
│   ├── test_parser.py          # 50/50 parsing, monotonic timestamps, 0 dropped lines
│   └── test_pipeline.py        # Validation repairs, hook offset, and cold judge checks
├── app.py                      # Minimal Streamlit app (script upload + provider runner)
├── run.py                      # CLI entrypoint for batch runs
├── NOTES.md                    # Running log of technical assumptions and AI failures
└── README.md                   # Public documentation and quick start
```

---

## 3. Critical Invariants for Agents

1. **Confidentiality**:
   - `assets/` and raw `.txt` screenplay files must **NEVER** be committed to Git. Ensure `.gitignore` ignores `assets/`, `*.zip`, and raw data folders.
   - The Streamlit app must support uploaded files so external evaluators can run the app without commiting proprietary scripts.
2. **Beat IDs vs. Floating Timestamps**:
   - The LLM should **NEVER** generate floating-point timestamps directly. LLMs hallucinate math.
   - The LLM receives indexed beat IDs (e.g. `[E01-B003]`) and outputs `start_beat_id`, `end_beat_id`, `hook_beat_id`, and `cliffhanger_beat_id`.
   - Python code in `src/validate.py` performs all timestamp math, window padding, and trimming.
3. **No Mid-Sentence Cuts**:
   - Cutpoints must align strictly with whole beat boundaries (`beat.start` to `beat.end`). Camera cuts (`shots`) provide cinematic cutpoint hints.
4. **Duration & Hook Bounds**:
   - Promo duration must strictly be **$\ge 20.0s$ and $\le 60.0s$**.
   - Hook beat start must occur within **$\le 3.0s$** of the clip start time.
5. **Cold-Viewer Isolation in Judging**:
   - `src/judge.py` must never receive earlier episode lore. It only receives the candidate clip transcript plus a **15-second post-cut peek** to test if tension actually stays unresolved.
6. **UI Scope Limitations**:
   - Do **NOT** build complex leaderboards, timelines, or video editors. Keep `app.py` minimal, clean, and focused on script upload, provider selection, and ranked promo display.

---

## 4. Runbook & Commands

### Virtual Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
```bash
PYTHONPATH=. ./.venv/bin/pytest tests/
```

### Running Benchmark Evaluation
```bash
PYTHONPATH=. ./.venv/bin/python3 eval/evaluate.py
```

### Running Full Pipeline via CLI
```bash
# Offline zero-cost mock:
PYTHONPATH=. ./.venv/bin/python3 run.py --provider mock

# Production run with Gemini Free Tier:
export GEMINI_API_KEY="your-gemini-key"
PYTHONPATH=. ./.venv/bin/python3 run.py --provider gemini

# Limit episodes for quick smoke testing:
PYTHONPATH=. ./.venv/bin/python3 run.py --provider mock --max-episodes 5
```

### Running Streamlit UI
```bash
./.venv/bin/streamlit run app.py
```

---

## 5. Telemetry & Cost Accounting

Every call made through `src/llm.py` is logged with:
- `prompt_tokens`
- `completion_tokens`
- `estimated_cost_usd` based on current provider rates.
Query global usage at any time with `get_usage_summary()`.
