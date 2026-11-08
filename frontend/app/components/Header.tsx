"use client";

import React from "react";
import { Search, Info, ShieldCheck, X } from "lucide-react";
import { RunMetadata } from "../types";

interface HeaderProps {
  meta: RunMetadata;
  activeTab: string;
  onTabChange: (tab: "ranked" | "episodes" | "stability" | "failures" | "sandbox") => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  meta,
  activeTab,
  onTabChange,
  searchQuery,
  onSearchChange,
}) => {
  const modelName = meta.api_model_version_returned || meta.model_requested || "gemini-3.5-flash-lite";

  return (
    <header className="w-full bg-white text-[#111111] z-50">
      {/* 1. Utility Bar (~36px, #f5f5f5, 12px text, right-aligned) */}
      <div className="w-full bg-[#f5f5f5] h-9 border-b border-[#cacacb]/40">
        <div className="max-w-[1440px] mx-auto h-full px-6 sm:px-8 flex items-center justify-between text-[11px] font-medium text-[#707072]">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-[#111111] tracking-wider uppercase">KUKU AI GENERALIST</span>
            <span className="hidden sm:inline">&middot;</span>
            <span className="hidden sm:inline">VERTICAL MICRODRAMA PROMO DISCOVERY</span>
          </div>

          <div className="flex items-center gap-4 text-[#111111]">
            <span>Model: <strong className="font-mono text-[#111111]">{modelName}</strong></span>
            <span>&middot;</span>
            <span>API Calls: <strong className="font-mono text-[#111111]">10 (All 50 Eps)</strong></span>
            <span>&middot;</span>
            <span>Free Tier: <strong className="font-mono text-[#007d48]">$0.00</strong> <span className="text-[#707072] text-[10px]">($0.022 est. paid)</span></span>
          </div>
        </div>
      </div>

      {/* 2. Primary Nav (56-64px, #ffffff, logo, centered links, right search pill) */}
      <div className="w-full bg-white h-16 border-b border-[#cacacb]/60 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-[1440px] mx-auto h-full px-6 sm:px-8 flex items-center justify-between">
          {/* Logo / Mark */}
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => onTabChange("ranked")}>
            <svg
              className="w-14 h-7 fill-[#111111]"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Minimal geometric swoosh-style mark */}
              <path d="M21.707 5.293a1 1 0 0 0-1.414 0L9 16.586l-4.293-4.293a1 1 0 0 0-1.414 1.414l5 5a1 1 0 0 0 1.414 0l12-12a1 1 0 0 0 0-1.414z" />
            </svg>
            <span className="font-black tracking-tighter text-lg uppercase font-display text-[#111111]">
              KUKU // COMMERCE
            </span>
          </div>

          {/* Centered Navigation Links with 2px bottom underline on active */}
          <nav className="hidden md:flex items-center gap-8 h-full">
            <button
              onClick={() => onTabChange("ranked")}
              className={`h-full flex items-center text-[15px] font-medium tracking-tight transition-colors relative cursor-pointer ${
                activeTab === "ranked"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              Top 15 Ranked Promos
            </button>

            <button
              onClick={() => onTabChange("episodes")}
              className={`h-full flex items-center text-[15px] font-medium tracking-tight transition-colors relative cursor-pointer ${
                activeTab === "episodes"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              All 50 Episodes
            </button>

            <button
              onClick={() => onTabChange("stability")}
              className={`h-full flex items-center text-[15px] font-medium tracking-tight transition-colors relative cursor-pointer ${
                activeTab === "stability"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              Stability &amp; Quota
            </button>

            <button
              onClick={() => onTabChange("failures")}
              className={`h-full flex items-center text-[15px] font-medium tracking-tight transition-colors relative cursor-pointer ${
                activeTab === "failures"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              Failure Analyses
            </button>

            <button
              onClick={() => onTabChange("sandbox")}
              className={`h-full flex items-center text-[15px] font-medium tracking-tight transition-colors relative cursor-pointer ${
                activeTab === "sandbox"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              Run It Yourself
            </button>
          </nav>

          {/* Right Search Pill + Quick Actions */}
          <div className="flex items-center gap-3">
            {/* Nike Search Pill: #f5f5f5, rounded-full (24px/30px), 40px height */}
            <div className="relative flex items-center">
              <Search className="w-4 h-4 text-[#707072] absolute left-3 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    const el = document.getElementById("main-content") || document.getElementById("ranked-section");
                    el?.scrollIntoView({ behavior: "smooth" });
                  }
                }}
                placeholder="Search episodes, quotes, #rank..."
                className="w-44 sm:w-64 h-10 bg-[#f5f5f5] text-[#111111] text-[13px] font-normal pl-9 pr-8 rounded-full border border-transparent focus:border-[#111111] focus:bg-white focus:outline-none transition-all placeholder:text-[#707072]"
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange("")}
                  className="absolute right-2.5 w-5 h-5 flex items-center justify-center rounded-full text-[#707072] hover:text-[#111111] hover:bg-[#e5e5e5] transition-colors cursor-pointer"
                  title="Clear search"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Confidentiality Strip (Neutral, clean, 1px divider) */}
      <div className="bg-[#f5f5f5] border-b border-[#cacacb]/40 py-2">
        <div className="max-w-[1440px] mx-auto px-6 sm:px-8 flex items-center justify-between text-xs text-[#707072]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#111111] shrink-0" />
            <span>
              <strong>Confidentiality Policy:</strong> Verbatim dialogue excerpts restricted to conservative &le; 8 words. Full unedited screenplay cutpoints reserved for private Drive submission.
            </span>
          </div>
          <span className="hidden md:inline font-mono text-[11px] text-[#707072]">
            Run 1 vs Run 2 IoU: 82.3%
          </span>
        </div>
      </div>
    </header>
  );
};
