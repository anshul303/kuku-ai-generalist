"use client";

import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-white border-t border-[#cacacb] mt-24 text-xs text-[#707072]">
      {/* 4 Columns Grid */}
      <div className="max-w-[1440px] mx-auto px-6 sm:px-8 py-16 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
        {/* Column 1 */}
        <div className="space-y-3">
          <h4 className="text-[13px] font-bold uppercase tracking-wider text-[#111111]">
            RESOURCES &amp; ENGINE
          </h4>
          <ul className="space-y-2.5">
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Deterministic Beat Parser</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Candidate Proposal Engine</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Duration &amp; Hook Repair</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Cold Judge &amp; Listwise Ranker</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Regex Baseline Engine</span></li>
          </ul>
        </div>

        {/* Column 2 */}
        <div className="space-y-3">
          <h4 className="text-[13px] font-bold uppercase tracking-wider text-[#111111]">
            PROMO CRITERIA
          </h4>
          <ul className="space-y-2.5">
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">0&ndash;3s Scroll-Stopping Hook</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">20.0s &ndash; 60.0s Strict Duration</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Unresolved Cliffhanger Cutpoint</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Cold-Viewer Standalone Coherence</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">15s Post-Cut Tension Peek</span></li>
          </ul>
        </div>

        {/* Column 3 */}
        <div className="space-y-3">
          <h4 className="text-[13px] font-bold uppercase tracking-wider text-[#111111]">
            QUOTA &amp; INVARIANTS
          </h4>
          <ul className="space-y-2.5">
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Free Tier Quota (~20 req/day)</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">10 API Calls per 50-Episode Run</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Exact Model: gemini-3.5-flash-lite</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Actual Cost: $0.00 Free Tier</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Est. Paid Tier: $0.0220 USD</span></li>
          </ul>
        </div>

        {/* Column 4 */}
        <div className="space-y-3">
          <h4 className="text-[13px] font-bold uppercase tracking-wider text-[#111111]">
            CONFIDENTIALITY &amp; SUBMISSION
          </h4>
          <ul className="space-y-2.5">
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">&le; 8-Word Dialogue Public Policy</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Private Submission Drive Folder</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Git-Ignored Assets &amp; Outputs</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Solution Doc (2-Page PDF)</span></li>
            <li><span className="hover:text-[#111111] transition-colors cursor-pointer">Documented Failures (failures.md)</span></li>
          </ul>
        </div>
      </div>

      {/* Clean Bottom Copyright Row */}
      <div className="border-t border-[#cacacb]/40 py-6">
        <div className="max-w-[1440px] mx-auto px-6 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#707072]">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-[#111111]">&copy; 2026 Kuku Studios. All rights reserved.</span>
            <span>&middot;</span>
            <span>I Married a Broken Soldier. He was a Duke (50 Episodes)</span>
          </div>

          <div className="text-[11px] text-[#707072]">
            Vertical Microdrama Promo Discovery Engine
          </div>
        </div>
      </div>
    </footer>
  );
};
