# Kuku AI Generalist Assignment — Development Notes & Assumptions

## Core Assumptions
1. **Confidentiality**: The raw screenplay dataset in `assets/` is private intellectual property. It is git-ignored and only processed locally or accepted via user upload in the prototype.
2. **Promo Definition & Hard Constraints**:
   - Total duration strictly between **20.0s and 60.0s**.
   - Hook occurs in the **first 3 seconds** (0.0 to 3.0s relative to clip start).
   - Cut points must align with natural beat boundaries (end of dialogue line or action block, never mid-sentence). Camera cuts serve as valid secondary cut boundaries.
   - Promos must be self-contained: viewers with zero prior lore must instantly understand the immediate emotional conflict.
3. **Beat vs Shot Separation**:
   - `shots` (`**CAMERA:**` blocks) represent camera framings/movements. They often overlap actions or dialogue. They provide cinematic anchor points and valid editing cut points.
   - `beats` (`dialogue`, `action`, `sfx`) represent the chronological narrative progression with unique IDs (e.g., `E01-B001`).
4. **Model Inversion / Pipeline Separation**:
   - Candidate generation uses beat-ID ranges (ensuring no hallucinated floating-point math from LLMs).
   - Code deterministically calculates and verifies timestamp ranges, padding/trimming beats as needed.
   - The cold-viewer judge sees only the clip script plus subsequent 15s (without earlier lore) to simulate a scrolling user's cold impression.

## AI Failures & Format Drift Log
*(Updated as we run and evaluate pipeline against 50 episodes)*

1. **Initial Format Observation**:
   - Some episodes have minor format variations: varying headers, spaces around colons (`NAME :` vs `NAME (Emotion):`), sound effects formatted with or without bolding, and occasional non-monotonic camera cut timestamps due to overlapping b-roll/reactions.

2. **Prompt Intent Collision with Script Content**:
   - Episode dialogues frequently contain emotion descriptors such as `(Cold, Commanding)` or growth terminology like `cold scrollers`.
   - Naive dispatch checking for substring `"cold"` or `"judge"` in prompt text caused candidate proposals to be routed to judge schemas.
   - Fixed by determining downstream task type strictly from the Pydantic/JSON schema properties (`candidates` vs `verdict` vs `rankings`), ensuring 100% deterministic intent matching regardless of script vocabulary.

3. **Array vs Object Format Normalization in Gemini Output**:
   - Gemini JSON mode (`gemini-3.5-flash`) often returns a raw top-level array `[{...}, {...}]` instead of wrapping in an object `{"candidates": [...]}`.
   - Unhandled list indexing caused type errors and triggered mock fallback.
   - Fixed by wrapping bare list returns into schema-compliant dictionary objects before metadata annotation and candidate parsing.

4. **Removal of Silent Mock Fallback**:
   - The engine previously caught provider exceptions and transparently substituted mock heuristic outputs.
   - In production auditing, this masked API quota failures (e.g. Free Tier 20 requests/day limit) as "successful runs".
   - Removed silent fallback: `--provider gemini` now strictly fails and surfaces the true upstream API status and error messages without obfuscation.
