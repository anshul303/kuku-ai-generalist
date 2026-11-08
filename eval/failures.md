# Evaluation: Failure Modes & Edge Case Analysis

This document details real failure modes observed during automated promo extraction on *I Married a Broken Soldier. He was a Duke*, including specific episodes, timestamps, root causes, run1 vs run2 evidence, and recommended mitigations.

---

### Failure 1: Cutting on Cathartic Payoff vs. Unresolved Cliffhanger (The Episode 45 Trap)
- **Episode**: Episode 45
- **Timestamps Picked by Tool**:
  - **Run 1**: `00:54.00 - 01:20.40` (Duration: 26.4s | Beat `E45-B024` to `E45-B032`)
  - **Run 2**: `00:54.00 - 01:53.00` (Duration: 59.0s | Beat `E45-B024` to `E45-B043`)
- **What the tool picked**:
  - Opens on Alexander's visceral confrontation: *"You poisoned my mother. You tortured my wife."*
  - In **Run 1**, the cut landed at `01:20.40`, directly after Alexander proclaims: *"Lady Juliana Ashcroft is my lawful wife... and the Duchess of Ashburton!"*
  - In **Run 2**, the cut drifted all the way to `01:53.00`, capturing Rupert's shellshocked reaction, Alexander walking through the crowd, and a bishop entering.
- **Why it failed**:
  - The model treated the grand climax proclamation as the cliffhanger.
  - In short-form video advertising, proclaiming the protagonist is the Duchess provides **cathartic resolution** to the viewer. When the mystery is answered inside the ad, viewer urgency to install the app or unlock Episode 46 drops sharply.
- **The Superior Alternative Cut**:
  - **`00:51.80 - 01:14.50` (Duration: 22.7s)**:
    - Opens with Alexander stepping up to Catherine in righteous fury (`00:51.80`), delivering the accusatory hook: *"You poisoned my mother. You tortured my wife."* (`00:54.00 - 00:58.00`).
    - Catherine gasps in horrified disbelief: *"Wife?!"* (`01:08.80 - 01:10.50`).
    - Alexander begins to address the congregation: *"Before the Crown and before God..."* (`01:11.50 - 01:14.00`).
    - **Cuts at `01:14.50` on Alexander's unfinished line**, right before he proclaims that she is the Duchess of Ashburton.
    - Cutting on the unfinished vow after Catherine's shock leaves the revelation suspended at peak unresolved tension without giving away the payoff.
- **Run 1 vs Run 2 Evidence**:
  - Between Run 1 (`26.4s`) and Run 2 (`59.0s`), run-to-run IoU dropped to **0.447**. Both runs shared the exact start hook (`00:54.00`), but the LLM suffered significant tail-boundary drift because it lacked a negative constraint against cutting after title/status reveals.
- **Mitigation**: Add a negative heuristic penalty in `src/judge.py` for cutting after full identity/title resolutions (*"I am the Duke / She is the Duchess"*); cut on the accusation or shock reaction preceding the reveal.

---

### Failure 2: 60-Second Window Drift & Proposal Boundary Instability (Episode 3)
- **Episode**: Episode 3
- **Timestamps Picked by Tool**:
  - **Run 1**: `01:09.90 - 02:09.90` (Duration: 60.0s | Beat `E03-B043` to `E03-B057`)
  - **Run 2**: `01:50.90 - 02:25.75` (Duration: 34.85s | Beat `E03-B053` to `E03-B057`)
- **What happened**:
  - In Episode 3, the cathedral guards seize Juliana. The scarred stranger shouts *"Take your hands off her!"* (`01:09.90`), steps in, drops to one knee, and proposes: *"Lady Juliana... accept my hand"* (`01:37.50 - 01:40.30`).
  - In **Run 1**, the model locked onto the maximum allowed upper bound (60.0s), extending the window from `01:09.90` to `02:09.90`. This captured unnecessary trailing ambient crowd murmur and dialogue well after the proposal peak.
  - In **Run 2**, the model drifted to `01:50.90 - 02:25.75`, completely missing the opening hook (*"Take your hands off her!"*) and capturing only the aftermath.
- **Run 1 vs Run 2 Evidence**:
  - Temporal overlap between Run 1 and Run 2 for Episode 3 was only **0.250 IoU** (the second-lowest across all 50 episodes: lowest was E41 at 0.177, then E03 at 0.250, then E46 at 0.344).
  - **Hypothesis (Window Maximization Bias)**: When given a $[20s, 60s]$ range, proposal prompts may tend to expand candidates toward 60s to aggregate context rather than snapping tightly to the 30–35s dramatic sweet spot.
- **Mitigation**: Implement an action-decay cutpoint detector: once a major climax beat (e.g., a proposal or physical confrontation) concludes and subsequent beats transition to dialogue tags with low emotional intensity, force the cut within $\le 3.0s$.

---

### Failure 3: Lore-Dependent Irony (High Intrinsic Drama, Zero Cold Context)
- **Episode**: Episode 8
- **Timestamps**: `00:16.30 - 00:48.50` (Duration: 32.2s)
- **What the tool picked**: Alexander discussing rare alpine herbs with Juliana beside the hearth, remarking that *"soldiers learn quickly which plants keep a man alive."*
- **Why it failed**:
  - The model proposed this because in the broader show narrative, this is a massive clue that the "crippled peasant soldier" is secretly the educated Duke Alexander of Ashbourne.
  - However, to a **cold viewer on TikTok**, the clip appears to be a mundane botanical gardening conversation. It lacks visceral antagonist conflict, a slap, or an overt emotional threat.
- **Root Cause**: LLM confused long-term dramatic irony (which requires knowing the Duke's backstory) with immediate short-form visceral hook power.
- **Mitigation**: Cold-viewer judge gate strictly penalizes clips where the conflict depends on unstated backstory lore.

---

### Failure 4: Visual Action without Dialogue (Text-Blindness)
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

### Failure 5: Deflated "Fake" Cliffhanger
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

### Failure 6: Rapid-Fire Multi-Speaker Interruptions & Cutpoint Drift
- **Episode**: Episode 3 (Mid-scene dialogue)
- **Timestamps**: `00:45.20 - 01:12.80` (Duration: 27.6s)
- **What the tool picked**: The cathedral confrontation where the Priest orders guards to seize Juliana.
- **Why it failed**:
  - Dialogue moves rapidly between 4 speakers in 5 seconds (Priest, Juliana, Gerald, Guard).
  - The original candidate cut occurred at `01:12.80`—right as the Stranger said *"Take your..."*, cutting mid-sentence because the 30-second duration target was hit.
- **Root Cause**: Duration-based windowing without whole-beat constraints truncated the sentence.
- **Mitigation**: `src/validate.py` now enforces that cuts occur **exclusively at whole beat boundaries** (`beat.end`), preventing mid-sentence clipping.

---

### Failure 7: Late-Season Culmination Spoilers
- **Episode**: Episode 49
- **Timestamps**: `00:12.00 - 00:52.00` (Duration: 40.0s)
- **What the tool picked**: The formal royal unmasking where the High Chancellor kneels before Alexander, proclaiming him the surviving Duke of Ashbourne, while Gerald is arrested for treason.
- **Why it failed**:
  - As a standalone scene, this has tremendous 10/10 stopping power and dramatic catharsis.
  - But posting this on Top-of-Funnel paid social destroys the entire 50-episode premise for new users, removing the curiosity that drives in-app chapter unlocks.
- **Root Cause**: Pure CTR-focused metrics ignore narrative lifecycle and funnel placement.
- **Mitigation**: Added a `spoiler_note` and funnel tiering tag in `src/judge.py`. Late-season climaxes (Episodes 30-50) are flagged for retargeting/re-engagement campaigns, while early episodes (1-10) are prioritized for cold user acquisition.

---

### Failure 8: Pronoun Ambiguity / Dangling Reference
- **Episode**: Episode 14
- **Timestamps**: `00:32.00 - 00:58.00` (Duration: 26.0s)
- **What the tool picked**: A heated argument where a visitor exclaims: *"He knew about the forged signature all along!"*
- **Why it failed**:
  - The clip began on beat 12 where the pronoun "He" was used, but the character was introduced in beat 9.
  - A cold viewer has no way of knowing whether "He" refers to Gerald, the Father, or Alexander.
- **Root Cause**: The clip start was trimmed to stay within duration limits without verifying that key third-person pronouns had an antecedent inside the window.
- **Mitigation**: In validation, when candidate starts with a pronoun ("He", "She", "They"), check if character name was spoken within the previous 1 beat or shift start backward.
