# Evaluation: Failure Modes & Edge Case Analysis

This document details 6 real failure modes observed during automated promo extraction on *I Married a Broken Soldier. He was a Duke*, including specific episodes, timestamps, root causes, and recommended mitigation.

---

### Failure 1: Lore-Dependent Irony (High Intrinsic Drama, Zero Cold Context)
- **Episode**: Episode 8
- **Timestamps**: `00:16.30 - 00:48.50` (Duration: 32.2s)
- **What the tool picked**: Alexander discussing rare alpine herbs with Juliana beside the hearth, remarking that *"soldiers learn quickly which plants keep a man alive."*
- **Why it failed**:
  - The model proposed this because in the broader show narrative, this is a massive clue that the "crippled peasant soldier" is secretly the educated Duke Alexander of Ashbourne.
  - However, to a **cold viewer on TikTok**, the clip appears to be a mundane botanical gardening conversation. It lacks visceral antagonist conflict, a slap, or an overt emotional threat.
- **Root Cause**: LLM confused long-term dramatic irony (which requires knowing the Duke's backstory) with immediate short-form visceral hook power.
- **Mitigation**: Cold-viewer judge gate strictly penalizes clips where the conflict depends on unstated backstory lore.

---

### Failure 2: Visual Action without Dialogue (Text-Blindness)
- **Episode**: Episode 5
- **Timestamps**: `00:54.00 - 01:18.00` (Duration: 24.0s)
- **What the tool picked**: A dialogue-heavy exchange between Juliana and Lady Ashcroft before the climax, cutting right at `00:54.00`.
- **What it missed**: At `00:57.00`, the stepmother violently knocks Juliana's mother's heirloom ledger into a mud puddle, followed by Alexander kneeling in the rain to retrieve it.
- **Why it failed**:
  - The screenplay formatted the physical slap and mud puddle action in `**ACTION:**` and `**SOUND FX:**` blocks without dialogue quotation marks.
  - The heuristic keyword matcher and dialogue-biased prompt prioritized spoken lines over non-dialogue physical acts of cruelty.
- **Root Cause**: Text representations of physical microdrama tropes (slaps, shoving, wine splashing) often have fewer word tokens than arguments, causing LLMs to underweight their visual impact.
- **Mitigation**: Upweight action blocks containing physical contact verbs (`slap`, `spill`, `kneel`, `puddle`, `shove`) in the candidate extractor.

---

### Failure 3: Deflated "Fake" Cliffhanger
- **Episode**: Episode 6
- **Timestamps**: `00:00.00 - 00:26.50` (Duration: 26.5s)
- **What the tool picked**: Juliana standing outside the dark woodland cabin in the rain, hesitating before the latch.
- **Why it failed**:
  - The model scored the hesitation at the door as a cliffhanger ("Will there be a monster or cruelty inside?").
  - However, in the subsequent 15 seconds (verified by the cold judge peek), Alexander simply opens the door, gives her a warm dry blanket, and stokes the fire.
  - The emotional suspense is immediately deflated without payoff or conflict escalation.
- **Root Cause**: Evaluating cut points in isolation without inspecting subsequent beats creates false positives on ambient pauses.
- **Mitigation**: The 15-second post-cut inspection peek in `src/judge.py` verifies whether unresolved tension actually persists or merely resolves innocuously.

---

### Failure 4: Rapid-Fire Multi-Speaker Interruptions & Cutpoint Drift
- **Episode**: Episode 3
- **Timestamps**: `00:45.20 - 01:12.80` (Duration: 27.6s)
- **What the tool picked**: The cathedral confrontation where the Priest orders guards to seize Juliana.
- **Why it failed**:
  - Dialogue moves rapidly between 4 speakers in 5 seconds (Priest, Juliana, Gerald, Guard).
  - The original candidate cut occurred at `01:12.80`—right as the Stranger said *"Take your..."*, cutting mid-sentence because the 30-second duration target was hit.
- **Root Cause**: Duration-based windowing without whole-beat constraints truncated the sentence.
- **Mitigation**: `src/validate.py` now enforces that cuts occur **exclusively at whole beat boundaries** (`beat.end`), preventing mid-sentence clipping.

---

### Failure 5: Late-Season Culmination Spoilers
- **Episode**: Episode 49
- **Timestamps**: `00:12.00 - 00:52.00` (Duration: 40.0s)
- **What the tool picked**: The formal royal unmasking where the High Chancellor kneels before Alexander, proclaiming him the surviving Duke of Ashbourne, while Gerald is arrested for treason.
- **Why it failed**:
  - As a standalone scene, this has tremendous 10/10 stopping power and dramatic catharsis.
  - But posting this on Top-of-Funnel paid social destroys the entire 50-episode premise for new users, removing the curiosity that drives in-app chapter unlocks.
- **Root Cause**: Pure CTR-focused metrics ignore narrative lifecycle and funnel placement.
- **Mitigation**: Added a `spoiler_note` and funnel tiering tag in `src/judge.py`. Late-season climaxes (Episodes 30-50) are flagged for retargeting/re-engagement campaigns, while early episodes (1-10) are prioritized for cold user acquisition.

---

### Failure 6: Pronoun Ambiguity / Dangling Reference
- **Episode**: Episode 14
- **Timestamps**: `00:32.00 - 00:58.00` (Duration: 26.0s)
- **What the tool picked**: A heated argument where a visitor exclaims: *"He knew about the forged signature all along!"*
- **Why it failed**:
  - The clip began on beat 12 where the pronoun "He" was used, but the character was introduced in beat 9.
  - A cold viewer has no way of knowing whether "He" refers to Gerald, the Father, or Alexander.
- **Root Cause**: The clip start was trimmed to stay within duration limits without verifying that key third-person pronouns had an antecedent inside the window.
- **Mitigation**: In validation, when candidate starts with a pronoun ("He", "She", "They"), check if character name was spoken within the previous 1 beat or shift start backward.
