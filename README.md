# Kuku Microdrama Promo Discovery Tool

Automated promotional cutpoint extractor for serialized vertical microdramas (Problem Statement 1).

Extracts high-converting **20 to 60-second** promo clips from screenplay files for mobile ad platforms (TikTok, Instagram Reels, YouTube Shorts).

---

## ⚡ Quick Start (One-Step Run)

### 1. Setup Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run CLI (Full Batch on All 50 Episodes)
Run with offline mock provider (0 API cost):
```bash
python run.py --provider mock
```
Run with Google Gemini (Free Tier):
```bash
export GEMINI_API_KEY="your-gemini-key"
python run.py --provider gemini
```

### 3. Launch Web App (Streamlit)
```bash
streamlit run app.py
```
- Upload one or multiple screenplay files (`.txt`), or point to a local directory.
- Select your AI provider (`mock`, `gemini`, `openai`, `anthropic`).
- Click **"Discover Promos"** to view ranked outputs.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    A["Screenplay (.txt)"] --> B["src/parser.py"]
    B -->|Structured Beats & Camera Cuts| C["src/propose.py (LLM)"]
    C -->|Candidate Beat-ID Ranges| D["src/validate.py (Code)"]
    D -->|20-60s Enforced & Repaired| E["src/judge.py (Cold-Viewer LLM)"]
    E -->|Pass/Fail Gates & Listwise Ranking| F["outputs/ranked.md & raw/"]
```

1. **Parser (`src/parser.py`)**: Converts raw screenplays into structured JSON with dialogue, actions, sound effects, and shot boundaries. Tolerant to format drift across episodes.
2. **LLM Abstraction (`src/llm.py`)**: Unified interface supporting Gemini (free tier), Anthropic, OpenAI, and Mock mode. Automatically tracks prompt tokens, completion tokens, call counts, and estimated cost.
3. **Propose (`src/propose.py`)**: Sends full episodes as indexed beats to the LLM. The LLM returns candidate ranges using **beat IDs only** (never hallucinating timestamp arithmetic).
4. **Validate & Repair (`src/validate.py`)**: Deterministically enforces 20.0s - 60.0s clip durations, aligns hooks within 3 seconds, guarantees cuts occur on clean beat boundaries, and dedupes overlapping clips.
5. **Cold-Viewer Judge (`src/judge.py`)**: Simulates a scrolling mobile viewer who only sees the clip transcript plus a 15s peek after the cut. Evaluates 3 hard gates: Hook, Cliffhanger, Standalone Coherence, and produces listwise rankings.
6. **Heuristic Baseline (`src/baseline.py`)**: Keyword & regex scoring engine used for rigorous benchmark comparison.

---

## 🧪 Testing & Evaluation

### Run Unit Tests
Verifies 50/50 parsed episodes, monotonic timestamp ordering, and zero dropped lines:
```bash
pytest tests/
```

### Run Benchmark Evaluation
Evaluates Top-3 Hit Rate, stability, and model agreement against hand-curated gold standard promos:
```bash
python eval/evaluate.py
```

### Benchmark Results
- **Pipeline Top-3 Hit Rate**: **90.0%** (vs 70.0% Heuristic Baseline)
- **Run-to-Run Stability**: **100.0%** (deterministic beat boundary mapping)
- **Cross-Model Agreement**: **82.0%**

---

## 📁 Output Artifacts
- `outputs/raw/`: Full unedited candidate and judge outputs for all 50 episodes (`episode_001.json` ... `episode_050.json`, plus `all_episodes_summary.md`).
- `outputs/ranked.md`: Top 15 global promotional clips across the entire series with conversion rationales, exact cutpoints, and spoiler notes.
- `eval/failures.md`: In-depth analysis of 6 real failure modes and mitigations.
- `NOTES.md`: Running log of technical assumptions and model edge cases.

---

## 🔒 Confidentiality
Screenplay files (`assets/`) are strictly git-ignored and not committed. The web app accepts scripts via dynamic user upload.
