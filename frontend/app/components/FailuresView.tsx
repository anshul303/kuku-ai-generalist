"use client";

import React from "react";
import { AlertTriangle, CheckCircle2, Split } from "lucide-react";

export const FailuresView: React.FC = () => {
  return (
    <section className="space-y-12">
      {/* Section Header: Nike 32px Heading-XL */}
      <div className="pb-2 border-b border-[#cacacb]/40">
        <h2 className="text-[28px] sm:text-[32px] font-medium uppercase tracking-tight text-[#111111]">
          DOCUMENTED FAILURE MODES &amp; MITIGATIONS
        </h2>
        <p className="text-sm text-[#707072] mt-1">
          Empirical analyses of model divergence from human editorial instinct, documented from Run 1 vs. Run 2 logs.
        </p>
      </div>

      {/* Case 1: Episode 45 */}
      <div className="bg-[#f5f5f5] p-8 border border-[#cacacb]/60 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#cacacb]/60">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#707072] block">
              CASE STUDY 01 &middot; TOP #1 RANKED DIVERGENCE
            </span>
            <h3 className="font-display text-3xl sm:text-4xl uppercase tracking-tight text-[#111111] font-normal mt-1">
              EPISODE 45: PAYOFF REVEAL VS. UNFINISHED CUT
            </h3>
          </div>
          <span className="h-8 px-4 rounded-full bg-white text-[#111111] border border-[#cacacb] text-xs font-medium flex items-center">
            Human vs. AI Cutpoint
          </span>
        </div>

        <p className="text-sm text-[#39393b] leading-relaxed max-w-4xl">
          In Episode 45, Alexander confronts the antagonists who humiliated Juliana. The AI and a human editor select very different cutpoints for maximum TikTok click-through:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tool Cut */}
          <div className="bg-white p-6 border border-[#cacacb] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#111111] flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#007d48]" /> Pipeline Cut (00:54.00 &ndash; 01:20.40 | 26.4s)
              </span>
              <span className="font-mono text-xs text-[#707072]">Beat E45-B032</span>
            </div>
            <p className="text-sm font-serif italic text-[#111111]">
              &ldquo;Lady Juliana Ashcroft is my lawful wife... and the Duchess of Ashburton!&rdquo;
            </p>
            <p className="text-xs text-[#707072] leading-relaxed pt-2 border-t border-[#f5f5f5]">
              <strong>Model Rationale:</strong> Prioritizes complete status reversal. The scroller experiences the dramatic payoff of knowing the underdog is actually royalty.
            </p>
          </div>

          {/* Editor Cut */}
          <div className="bg-white p-6 border border-[#cacacb] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#111111] flex items-center gap-1.5">
                <Split className="w-4 h-4 text-[#111111]" /> Editor Alternative (00:51.80 &ndash; 01:14.50 | 22.7s)
              </span>
              <span className="font-mono text-xs text-[#707072]">Beat E45-B029</span>
            </div>
            <p className="text-sm font-serif italic text-[#111111]">
              &ldquo;Before the Crown and before God...&rdquo;
            </p>
            <p className="text-xs text-[#707072] leading-relaxed pt-2 border-t border-[#f5f5f5]">
              <strong>Human Editor Rationale:</strong> Cuts mid-sentence before the declaration. The scroller is forced to click the ad to learn what title Alexander is about to declare.
            </p>
          </div>
        </div>
      </div>

      {/* Case 2: Episode 3 */}
      <div className="bg-[#f5f5f5] p-8 border border-[#cacacb]/60 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#cacacb]/60">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#707072] block">
              CASE STUDY 02 &middot; WINDOW DRIFT INVESTIGATION
            </span>
            <h3 className="font-display text-3xl sm:text-4xl uppercase tracking-tight text-[#111111] font-normal mt-1">
              EPISODE 3: 60.0S TRIM VS. 34.85S DIRECT PROPOSAL
            </h3>
          </div>
          <span className="h-8 px-4 rounded-full bg-white text-[#111111] border border-[#cacacb] text-xs font-medium flex items-center">
            Run-to-Run IoU: 0.250
          </span>
        </div>

        <p className="text-sm text-[#39393b] leading-relaxed max-w-4xl">
          Episode 3 exhibited substantial run-to-run drift. Lowest overlaps across all 50 episodes were E41 (0.177), then E03 (0.250), then E46 (0.344). Tracing the telemetry revealed the exact mechanics:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 border border-[#cacacb] space-y-2 font-mono text-xs">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#111111] font-sans block mb-2">
              Run 1 (Window Maximization &amp; Trim)
            </span>
            <p className="text-[#707072]">Proposed Range: <strong className="text-[#111111]">E03-B030 to E03-B057 (75.8s)</strong></p>
            <p className="text-[#707072]">Validation Action: <strong className="text-[#111111]">TRIM_DURATION (-5 trailing beats)</strong></p>
            <p className="text-[#707072]">Final Cutpoint: <strong className="text-[#111111]">01:09.90 &ndash; 02:09.90 (60.0s max limit)</strong></p>
          </div>

          <div className="bg-white p-6 border border-[#cacacb] space-y-2 font-mono text-xs">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#111111] font-sans block mb-2">
              Run 2 (Direct Proposal)
            </span>
            <p className="text-[#707072]">Proposed Range: <strong className="text-[#111111]">E03-B047 to E03-B057 (34.85s)</strong></p>
            <p className="text-[#707072]">Validation Action: <strong className="text-[#111111]">0 repairs (Direct pass)</strong></p>
            <p className="text-[#707072]">Final Cutpoint: <strong className="text-[#111111]">01:35.05 &ndash; 02:09.90 (34.85s)</strong></p>
          </div>
        </div>

        <p className="text-xs text-[#707072] bg-white p-4 border border-[#e5e5e5] leading-relaxed">
          <strong className="text-[#111111]">Key Takeaway:</strong> Window maximization bias is a <em>hypothesis</em>: LLMs sometimes attempt to capture broad narrative arcs until clamped by hard duration bounds. Both runs agreed on the cliffhanger cut (Beat E03-B057), but differed on the opening hook beat.
        </p>
      </div>

      {/* Case 3 & 4: Score Clustering & Cold Judge */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 space-y-3 text-xs">
          <h4 className="text-sm font-bold uppercase tracking-tight text-[#111111]">
            Score Clustering at 8.0/10
          </h4>
          <p className="text-[#39393b] leading-relaxed">
            In unconstrained pointwise scoring, LLMs assign 8/10 to nearly any competent clip. Our run verified only <strong>2.0% (2 / 99)</strong> scored exactly 8.0 because:
          </p>
          <ul className="list-disc list-inside text-[#707072] space-y-1">
            <li>Strict 3-attribute rubrics (0–3s hook, cliffhanger tension, zero-lore coherence)</li>
            <li>Listwise ranking pass compares passing clips head-to-head to break ties</li>
          </ul>
        </div>

        <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 space-y-3 text-xs">
          <h4 className="text-sm font-bold uppercase tracking-tight text-[#111111]">
            Cold-Viewer Lore Isolation
          </h4>
          <p className="text-[#39393b] leading-relaxed">
            TikTok ad viewers know nothing about the series lore. The judging engine:
          </p>
          <ul className="list-disc list-inside text-[#707072] space-y-1">
            <li>Never receives earlier episode lore or character backstories</li>
            <li>Receives only candidate transcript + 15s post-cut peek to verify tension stays unresolved</li>
          </ul>
        </div>
      </div>
    </section>
  );
};
