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
