"use client";

import React, { useState } from "react";
import { Copy, Check, ArrowUpRight, Zap, Sparkles, Search, X } from "lucide-react";
import { PromoCandidate, EpisodeData } from "../types";
import { matchesPromo, matchesEpisode } from "../utils/search";

interface RankedPromosProps {
  topPromos: PromoCandidate[];
  onSelectEpisode: (epNum: number) => void;
  searchQuery: string;
  durationFilter: "all" | "short" | "medium" | "long";
  sortBy: "rank" | "score" | "duration";
  allEpisodes?: EpisodeData[];
  onClearSearch?: () => void;
}

// Fire rating classifier to visually resemble virality & hook heat
const getFireRating = (score: number) => {
  if (score >= 8.8) {
    return {
      emojis: "🔥🔥🔥",
      label: "Ultra Hot",
      badgeBg: "bg-amber-100 text-amber-950 border-amber-300",
      tagColor: "text-amber-800",
    };
  } else if (score >= 8.4) {
    return {
      emojis: "🔥🔥",
      label: "High Heat",
      badgeBg: "bg-amber-50 text-amber-900 border-amber-200",
      tagColor: "text-amber-700",
    };
  } else if (score >= 7.5) {
    return {
      emojis: "🔥",
      label: "Solid Hook",
      badgeBg: "bg-orange-50 text-orange-950 border-orange-200",
      tagColor: "text-orange-700",
    };
  } else {
    return {
      emojis: "⚡",
      label: "Passing Cut",
      badgeBg: "bg-neutral-100 text-neutral-800 border-neutral-300",
      tagColor: "text-neutral-600",
    };
  }
};

export const RankedPromos: React.FC<RankedPromosProps> = ({
  topPromos,
  onSelectEpisode,
  searchQuery,
  durationFilter,
  sortBy,
  allEpisodes = [],
  onClearSearch,
}) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (promo: PromoCandidate) => {
    const text = `Episode ${promo.episode}: ${promo.start_formatted} - ${promo.end_formatted} (${promo.duration}s)`;
    navigator.clipboard.writeText(text);
    const key = `${promo.episode}-${promo.start_formatted}`;
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Filter & sort
  let list = topPromos.filter((p) => {
    if (durationFilter === "short" && p.duration > 30) return false;
    if (durationFilter === "medium" && (p.duration <= 30 || p.duration > 45)) return false;
    if (durationFilter === "long" && p.duration <= 45) return false;

    if (searchQuery.trim()) {
      return matchesPromo(p, searchQuery);
    }
    return true;
  });

  if (sortBy === "score") {
    list = [...list].sort((a, b) => (b.composite_score || 0) - (a.composite_score || 0));
  } else if (sortBy === "duration") {
    list = [...list].sort((a, b) => a.duration - b.duration);
  }

  // Cross-search all 50 episodes when top 15 has no direct match
  const matchingOtherEpisodes = searchQuery.trim()
    ? allEpisodes.filter((ep) => matchesEpisode(ep, searchQuery))
    : [];

  return (
    <section className="space-y-10">
      {/* Section Header: Clean Nike Typography 32px Heading-XL */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-3 border-b border-[#cacacb]/60">
        <div>
          <h2 className="text-[28px] sm:text-[32px] font-medium uppercase tracking-tight text-[#111111]">
            FEATURED PROMO CUTPOINTS ({list.length})
          </h2>
          <p className="text-sm text-[#707072] mt-1">
            Top 15 short-form ad cutpoints discovered across all 50 episodes. Cold-viewer isolated, 20–60s duration validated.
          </p>
        </div>

        {searchQuery.trim() && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#707072]">
              Filtering by: <strong className="text-[#111111]">&ldquo;{searchQuery}&rdquo;</strong>
            </span>
            {onClearSearch && (
              <button
                onClick={onClearSearch}
                className="text-xs text-[#d30005] hover:underline cursor-pointer flex items-center gap-0.5"
              >
                <X className="w-3.5 h-3.5" /> Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* 3-Up Product Grid with distinct borders and card framing */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {list.map((promo, idx) => {
          const rank = promo.rank || idx + 1;
          const copyKey = `${promo.episode}-${promo.start_formatted}`;
          const isCopied = copiedKey === copyKey;

          // Warm colors specifically for the number boxes only (no full-heading color)
          let rankNumberBox = (
            <span className="bg-[#f5f5f5] text-[#111111] border border-[#cacacb] text-[12px] font-mono font-bold px-3 py-1 rounded-full uppercase">
              Rank #{rank}
            </span>
          );
          let episodeNumberBox = (
            <span className="bg-[#e5e5e5] text-[#111111] border border-[#cacacb] px-2.5 py-0.5 rounded font-mono font-bold text-2xl sm:text-3xl">
              {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
            </span>
          );
          let cardBorderClass = "border border-[#cacacb] hover:border-[#111111]";

          if (rank === 1) {
            rankNumberBox = (
              <span className="bg-gradient-to-br from-amber-500 via-amber-600 to-orange-500 text-white text-[12px] font-bold px-3 py-1 rounded-full shadow-sm ring-1 ring-amber-300/50 flex items-center gap-1.5 uppercase tracking-wide">
                <Sparkles className="w-3.5 h-3.5 text-amber-100" />
                #1 Ranked
              </span>
            );
            episodeNumberBox = (
              <span className="bg-amber-100 text-amber-950 border border-amber-300 px-2.5 py-0.5 rounded font-mono font-bold text-2xl sm:text-3xl shadow-xs">
                {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
              </span>
            );
            cardBorderClass = "border-2 border-amber-400/80 hover:border-amber-500 shadow-sm";
          } else if (rank === 2) {
            rankNumberBox = (
              <span className="bg-gradient-to-br from-orange-400 via-rose-400 to-amber-500 text-white text-[12px] font-bold px-3 py-1 rounded-full shadow-sm ring-1 ring-orange-200/50 flex items-center gap-1.5 uppercase tracking-wide">
                <Sparkles className="w-3.5 h-3.5 text-orange-100" />
                #2 Ranked
              </span>
            );
            episodeNumberBox = (
              <span className="bg-orange-100 text-orange-950 border border-orange-300 px-2.5 py-0.5 rounded font-mono font-bold text-2xl sm:text-3xl shadow-xs">
                {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
              </span>
            );
            cardBorderClass = "border-2 border-orange-300/80 hover:border-orange-400 shadow-sm";
          } else if (rank === 3) {
            rankNumberBox = (
              <span className="bg-gradient-to-br from-amber-600 to-yellow-600 text-white text-[12px] font-bold px-3 py-1 rounded-full shadow-sm ring-1 ring-amber-400/50 flex items-center gap-1.5 uppercase tracking-wide">
                <Sparkles className="w-3.5 h-3.5 text-amber-100" />
                #3 Ranked
              </span>
            );
            episodeNumberBox = (
              <span className="bg-yellow-100 text-yellow-950 border border-yellow-300 px-2.5 py-0.5 rounded font-mono font-bold text-2xl sm:text-3xl shadow-xs">
                {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
              </span>
            );
            cardBorderClass = "border-2 border-yellow-400/70 hover:border-yellow-500 shadow-sm";
          }

          return (
            <div
              key={promo.clip_id || `${promo.episode}-${promo.start_time}`}
              className={`group flex flex-col justify-between bg-white p-4 sm:p-5 transition-all duration-200 ${cardBorderClass}`}
            >
              <div>
                {/* Compact Aspect Mockup Stage on #f5f5f5 (Reduced dead empty space) */}
                <div className="w-full aspect-[16/10] bg-[#f5f5f5] relative overflow-hidden flex flex-col justify-between p-3.5 border border-[#e5e5e5]">
                  {/* Top Bar inside image: Warm Number Box on Rank, and Duration Pill */}
                  <div className="flex items-center justify-between w-full z-10">
                    {rankNumberBox}

                    <span className="bg-white text-[#111111] text-[11px] font-mono font-medium px-2.5 py-1 rounded-full border border-[#cacacb]">
                      {promo.duration.toFixed(1)}s
                    </span>
                  </div>

                  {/* Compact Editorial Centerpiece */}
                  <div className="my-auto text-center px-2 select-none">
                    <div className="inline-flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold uppercase tracking-widest text-[#707072]">
                        EPISODE
                      </span>
                      {episodeNumberBox}
                    </div>

                    <div className="bg-white border border-[#e5e5e5] px-3 py-1.5 text-left shadow-2xs">
                      <span className="text-[9px] uppercase font-bold tracking-wider text-[#707072] block">
                        Hook &le; 3.0s Excerpt
                      </span>
                      <p className="text-xs font-serif text-[#111111] italic truncate">
                        &ldquo;{promo.hook_text_safe}&rdquo;
                      </p>
                    </div>
                  </div>

                  {/* Card Bottom Overlay: Tension Progress Bar */}
                  <div className="w-full z-10">
                    <div className="flex justify-between text-[10px] font-mono text-[#707072] mb-1">
                      <span>00.0s (Hook)</span>
                      <span>Cut: {promo.end_formatted}</span>
                    </div>
                    <div className="h-1.5 w-full bg-[#e5e5e5] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#111111]"
                        style={{ width: `${Math.min(100, Math.max(20, (promo.duration / 60) * 100))}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Swatch Dot Row directly below image */}
                <div className="flex items-center gap-2 mt-3 mb-2">
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-[#111111] p-[2px] flex items-center justify-center">
                    <div className="w-full h-full rounded-full bg-[#111111]"></div>
                  </div>
                  <div className="w-2.5 h-2.5 rounded-full bg-[#cacacb]"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-[#e5e5e5]"></div>
                  <span className="text-[11px] text-[#707072] ml-1 font-mono">
                    {promo.repairs && promo.repairs.length > 0 ? "Repaired Window" : "Clean Beat Boundary"}
                  </span>
                </div>

                {/* Partitioning Divider: Stage & Title */}
                <div className="border-t border-[#e5e5e5] pt-2.5 mb-2" />

                {/* Bold Episode Title & Timing */}
                <div className="space-y-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <h3 className="text-lg font-bold text-[#111111] tracking-tight">
                      Episode {promo.episode}
                    </h3>
                    <span className="text-xs font-mono font-bold text-[#111111] bg-[#f5f5f5] px-2 py-0.5 rounded border border-[#cacacb]">
                      {promo.start_formatted} &ndash; {promo.end_formatted}
                    </span>
                  </div>
                  <p className="text-xs text-[#707072] leading-tight">
                    Vertical Microdrama Cut &middot; {promo.duration.toFixed(1)}s Runtime
                  </p>
                </div>

                {/* Partitioning Divider: Title & Rating */}
                <div className="border-t border-[#e5e5e5] my-2.5" />

                {/* Bold Ratings with Fire Emojis & Virality Theme */}
                {(() => {
                  const fire = getFireRating(promo.composite_score || 8.5);
                  return (
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-[#111111]">
                          Rating:
                        </span>
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded border font-mono font-extrabold text-xs shadow-2xs ${fire.badgeBg}`}>
                          <span>{fire.emojis}</span>
                          <span>{(promo.composite_score || 8.5).toFixed(1)} / 10</span>
                        </span>
                        <span className={`text-[11px] font-bold uppercase tracking-wide ${fire.tagColor}`}>
                          {fire.label}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-[#707072]">
                        Hook: <strong className="text-[#111111]">{(promo.hook_score || 8.5).toFixed(1)}</strong> &middot; Cliff: <strong className="text-[#111111]">{(promo.cliffhanger_score || 8.5).toFixed(1)}</strong>
                      </span>
                    </div>
                  );
                })()}

                {/* Partitioning Divider: Rating & Dialogue Excerpts */}
                <div className="border-t border-[#e5e5e5] my-2.5" />

                {/* Dialogue Excerpts Block */}
                <div className="bg-[#f5f5f5]/80 p-2.5 border border-[#e5e5e5] space-y-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block mb-0.5">
                      🪝 0–3s Hook Excerpt
                    </span>
                    <p className="text-xs font-serif italic text-[#111111] line-clamp-1">
                      &ldquo;{promo.hook_text_safe}&rdquo;
                    </p>
                  </div>
                  <div className="border-t border-[#e5e5e5] pt-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block mb-0.5">
                      ⚡ Cliffhanger Cutpoint
                    </span>
                    <p className="text-xs font-serif italic text-[#111111] line-clamp-1">
                      &ldquo;{promo.cliffhanger_text_safe}&rdquo;
                    </p>
                  </div>
                </div>

                {/* Partitioning Divider: Excerpts & Description */}
                <div className="border-t border-[#e5e5e5] my-2.5" />

                {/* Partitioned Description / Conversion Rationale */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block">
                    Why It Converts &middot; Rationale
                  </span>
                  <p className="text-xs text-[#39393b] leading-relaxed line-clamp-2">
                    {promo.rationale || "High-friction emotional confrontation stops feeds cold."}
                  </p>
                </div>
              </div>

              {/* Action Buttons: Nike Two-Tone Button Hierarchy with Top Divider */}
              <div className="pt-3.5 mt-4 border-t border-[#cacacb]/60 flex items-center gap-2">
                <button
                  onClick={() => onSelectEpisode(promo.episode)}
                  className="flex-1 h-10 px-4 bg-[#111111] text-white rounded-full text-xs font-medium hover:bg-neutral-800 active:scale-95 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  Inspect Episode {promo.episode}
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={() => handleCopy(promo)}
                  className="h-10 px-4 bg-[#f5f5f5] text-[#111111] rounded-full text-xs font-medium hover:bg-[#e5e5e5] active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer border border-[#cacacb]/70"
                  title="Copy timestamps"
                >
                  {isCopied ? <Check className="w-3.5 h-3.5 text-[#007d48]" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{isCopied ? "Copied" : "Copy"}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {list.length === 0 && (
        <div className="py-16 px-6 text-center bg-[#f5f5f5] rounded-none border border-[#cacacb] space-y-4">
          <p className="text-base font-bold text-[#111111]">
            No Top 15 ranked promos matched {searchQuery.trim() ? <>&ldquo;{searchQuery}&rdquo;</> : "your filter"}.
          </p>

          {matchingOtherEpisodes.length > 0 ? (
            <div className="space-y-4 max-w-xl mx-auto pt-2">
              <p className="text-sm text-[#39393b]">
                However, <strong>{matchingOtherEpisodes.length} episode(s)</strong> matched your search in the complete 50-episode catalog:
              </p>
              <div className="flex flex-wrap justify-center gap-2.5">
                {matchingOtherEpisodes.map((ep) => (
                  <button
                    key={ep.episode}
                    onClick={() => onSelectEpisode(ep.episode)}
                    className="h-10 px-5 bg-[#111111] text-white rounded-full text-xs font-semibold hover:bg-neutral-800 active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
                  >
                    <span>View Episode {ep.episode < 10 ? `0${ep.episode}` : ep.episode}</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-[#707072]">
                Try searching by an episode number (e.g. &ldquo;3&rdquo;, &ldquo;45&rdquo;), character name (&ldquo;Juliana&rdquo;, &ldquo;Alexander&rdquo;), or dramatic quote.
              </p>
              {onClearSearch && searchQuery.trim() && (
                <button
                  onClick={onClearSearch}
                  className="h-9 px-5 bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111] rounded-full text-xs font-semibold cursor-pointer"
                >
                  Clear Search Filter
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
};
