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

5. **Quota Ceiling Architecture & The Necessity of Call Batching**:
   - **The Quota Ceiling**: The Gemini Developer API Free Tier enforces a strict rate limit of approximately 15–20 requests per day per model family on standard flash models (`gemini-3.5-flash` / `gemini-3.6-flash`). A naive architecture that invokes 1 LLM proposal call per episode + 2-3 judge calls per episode would require ~150-200 calls, exhausting the daily free quota within the first 5-8 episodes.
   - **Why Batching Was Implemented**: We restructured the entire 50-episode discovery pipeline into:
     - **Propose Stage**: 5 batched calls (~10 episodes per prompt, returning indexed beat-ID ranges for each episode).
     - **Judge Stage**: 4 batched calls (~25-30 candidate clips per prompt, evaluated against cold-viewer gates).
     - **Rank Stage**: 1 global listwise ranking call over survivors.
     - **Total Calls**: Exactly 10 calls for the entire 50-episode run, well beneath the $\le 12$ call ceiling.
   - **Disk Caching & State Checkpointing**: All LLM calls are cached to `.cache/llm_cache` using SHA-256 hashes of `(provider, model, params, prompt)`. Progress is checkpointed after each batch to `checkpoint.json`. If a network error or rate limit occurs, execution resumes from the exact batch without burning quota.

6. **Limitation of Batched Judging (Relative Cross-Contamination & Anchoring Bias)**:
   - In an ideal unconstrained environment, each candidate clip should be evaluated by an isolated LLM instance with zero exposure to other candidates.
   - In batched judging (where 25-30 candidate clips are presented together in a single prompt alongside their individual 15-second post-cut peeks), the LLM inevitably compares clips within the batch rather than judging each against an absolute objective standard.
   - **Consequences**:
     - *Anchoring Bias*: A mediocre clip appearing immediately after a very weak clip may receive higher scores than if evaluated alone.
     - *Relative Grading*: The judge may distribute pass/fail verdicts to create artificial variance within the batch rather than evaluating each strictly against the $\ge 6.5$ threshold.
   - **Mitigation Applied**: Each candidate's prompt section is explicitly fenced with independent context boundaries, and prompt instructions enforce per-clip invariant evaluation before generating JSON verdicts.

7. **Model Gateway Routing & Name Mismatch Explained**:
   - When requesting `models/gemini-3.5-flash`, the Google Gemini API gateway internally routed the request to its `gemini-3.6-flash` production cluster, surfacing quota failure headers referring to `models/gemini-3.6-flash`.
   - Separate quota pools exist across model IDs: switching to `gemini-3.5-flash-lite` accessed an independent, unexhausted free-tier quota pool, completing all 50 episodes with zero quota exhaustion.
