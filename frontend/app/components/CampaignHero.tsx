"use client";

import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";

interface CampaignHeroProps {
  onExploreTop: () => void;
  onBrowseAll: () => void;
}

export const CampaignHero: React.FC<CampaignHeroProps> = ({
  onExploreTop,
  onBrowseAll,
}) => {
  return (
    <section className="w-full bg-[#111111] relative overflow-hidden mb-12">
      {/* Cinematic Editorial Background with rich vignette & dramatic lighting */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-800 via-neutral-950 to-[#111111] opacity-90"></div>

      {/* Subtle high-contrast diagonal architectural lines reminiscent of high-end athletic fashion editorials */}
      <div className="absolute inset-0 opacity-15 pointer-events-none mix-blend-overlay">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#ffffff" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="max-w-[1440px] mx-auto px-6 sm:px-8 py-16 sm:py-24 relative z-10 flex flex-col justify-between min-h-[440px] sm:min-h-[520px]">
        {/* Top Tagline */}
        <div className="flex items-center gap-2">
          <span className="bg-white text-[#111111] text-[12px] font-bold uppercase tracking-widest px-3 py-1 rounded-full">
            SERIES 01 // 50 EPISODES
          </span>
          <span className="text-white/80 text-xs font-mono tracking-wider">
            I MARRIED A BROKEN SOLDIER. HE WAS A DUKE.
          </span>
        </div>

        {/* Towering 96px Uppercase Display Headline */}
        <div className="my-8">
          <h1 className="font-display text-[56px] sm:text-[84px] md:text-[104px] uppercase text-white leading-[0.88] tracking-tight max-w-4xl font-normal drop-shadow-sm select-none">
            FIND THE ADS THAT STOP THE SCROLL.
          </h1>
          <p className="mt-4 text-white/80 text-base sm:text-lg max-w-2xl font-normal tracking-tight">
            Automated promotional discovery across 50 vertical screenplays. High-converting 20–60s cutpoints engineered for TikTok, Reels, and Shorts ad arbitrage.
          </p>
        </div>

        {/* Nike On-Image Pill CTAs Anchored Bottom-Left */}
        <div className="flex flex-wrap items-center gap-3 pt-4">
          {/* button-outline-on-image: crisp white pill, black text */}
          <button
            onClick={onExploreTop}
            className="h-12 px-8 bg-white text-[#111111] rounded-full text-sm font-medium hover:bg-neutral-100 active:scale-95 transition-all flex items-center gap-2 cursor-pointer shadow-sm"
          >
            Explore Top 15 Promos
            <ArrowRight className="w-4 h-4" />
          </button>

          {/* Secondary translucent pill */}
          <button
            onClick={onBrowseAll}
            className="h-12 px-8 bg-transparent text-white border border-white/60 hover:border-white rounded-full text-sm font-medium hover:bg-white/10 active:scale-95 transition-all cursor-pointer"
          >
            Browse All 50 Episodes
          </button>
        </div>
      </div>
    </section>
  );
};
