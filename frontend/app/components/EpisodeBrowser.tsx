"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ArrowRight,
  X,
  Target,
} from "lucide-react";
import { EpisodeData, PromoCandidate } from "../types";
import { matchesEpisode, matchesPromo } from "../utils/search";

interface EpisodeBrowserProps {
  episodes: EpisodeData[];
  selectedEpisodeNum: number;
  onSelectEpisode: (epNum: number) => void;
  topPromoEpisodeMap: Record<number, number>;
  searchQuery: string;
  onSearchChange?: (q: string) => void;
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

export const EpisodeBrowser: React.FC<EpisodeBrowserProps> = ({
  episodes,
  selectedEpisodeNum,
  onSelectEpisode,
  topPromoEpisodeMap,
  searchQuery,
  onSearchChange,
  onClearSearch,
}) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const filteredEpisodes = episodes.filter((ep) => matchesEpisode(ep, searchQuery));

  // Automatically sync selected episode when search results change
  useEffect(() => {
    if (searchQuery.trim() && filteredEpisodes.length > 0) {
      const isCurrentInFiltered = filteredEpisodes.some((e) => e.episode === selectedEpisodeNum);
      if (!isCurrentInFiltered) {
        onSelectEpisode(filteredEpisodes[0].episode);
      }
    }
  }, [searchQuery, filteredEpisodes, selectedEpisodeNum, onSelectEpisode]);

  const selectedEpisode =
    filteredEpisodes.find((e) => e.episode === selectedEpisodeNum) ||
    (filteredEpisodes.length > 0 ? filteredEpisodes[0] : null);

  const handleCopy = (promo: PromoCandidate) => {
    const text = `Episode ${promo.episode}: ${promo.start_formatted} - ${promo.end_formatted} (${promo.duration}s)`;
    navigator.clipboard.writeText(text);
    const key = `${promo.episode}-${promo.start_formatted}`;
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handlePrev = () => {
    if (!filteredEpisodes.length) return;
    const currentIdx = filteredEpisodes.findIndex((e) => e.episode === selectedEpisode?.episode);
    if (currentIdx > 0) {
      onSelectEpisode(filteredEpisodes[currentIdx - 1].episode);
    }
  };

  const handleNext = () => {
    if (!filteredEpisodes.length) return;
    const currentIdx = filteredEpisodes.findIndex((e) => e.episode === selectedEpisode?.episode);
    if (currentIdx >= 0 && currentIdx < filteredEpisodes.length - 1) {
      onSelectEpisode(filteredEpisodes[currentIdx + 1].episode);
    }
  };

  return (
    <section className="space-y-8">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-3 border-b border-[#cacacb]/60">
        <div>
          <h2 className="text-[28px] sm:text-[32px] font-medium uppercase tracking-tight text-[#111111]">
            SERIES CATALOG &middot; ALL 50 EPISODES
          </h2>
          <p className="text-sm text-[#707072] mt-1">
            Browse discovered candidates, deterministic boundary repairs, and cold judge scores for all 50 episodes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {searchQuery.trim() && onClearSearch && (
            <button
              onClick={onClearSearch}
              className="h-10 px-4 bg-white text-[#d30005] border border-[#cacacb] hover:border-[#d30005] rounded-full text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer mr-2"
            >
              <X className="w-3.5 h-3.5" /> Clear Search
            </button>
          )}

          <button
            onClick={handlePrev}
            disabled={!filteredEpisodes.length || filteredEpisodes.findIndex((e) => e.episode === selectedEpisode?.episode) <= 0}
            className="h-10 px-4 bg-[#f5f5f5] text-[#111111] border border-[#cacacb] rounded-full text-xs font-medium hover:bg-[#e5e5e5] disabled:opacity-40 transition-all flex items-center gap-1 cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" /> Prev
          </button>
          <button
            onClick={handleNext}
            disabled={!filteredEpisodes.length || filteredEpisodes.findIndex((e) => e.episode === selectedEpisode?.episode) >= filteredEpisodes.length - 1}
            className="h-10 px-4 bg-[#f5f5f5] text-[#111111] border border-[#cacacb] rounded-full text-xs font-medium hover:bg-[#e5e5e5] disabled:opacity-40 transition-all flex items-center gap-1 cursor-pointer"
          >
            Next <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Grid: Left Filter Rail + Right Details Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Left Filter Rail (~220px to 1/4 col on desktop) */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-[#f5f5f5] p-5 border-2 border-[#cacacb] shadow-xs">
            <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-[#cacacb]/60">
              <span className="text-xs font-bold uppercase tracking-wider text-[#111111]">
                Episodes (1&ndash;50)
              </span>
              <span className="text-[11px] font-mono text-[#707072]">
                {filteredEpisodes.length} Shown
              </span>
            </div>

            {/* Quick sidebar filter input */}
            {onSearchChange && (
              <div className="relative flex items-center mb-3">
                <Search className="w-3.5 h-3.5 text-[#707072] absolute left-2.5 pointer-events-none" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  placeholder="Filter (e.g. 3, quote)..."
                  className="w-full h-8 bg-white text-[#111111] text-xs pl-8 pr-7 rounded border border-[#cacacb] focus:border-[#111111] focus:outline-none transition-all placeholder:text-[#707072]"
                />
                {searchQuery && onClearSearch && (
                  <button
                    onClick={onClearSearch}
                    className="absolute right-2 text-[#707072] hover:text-[#111111] cursor-pointer"
                    title="Clear filter"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}

            <div className="grid grid-cols-5 gap-1.5 max-h-[500px] overflow-y-auto pr-1">
              {filteredEpisodes.map((ep) => {
                const isSelected = ep.episode === selectedEpisodeNum;
                const topRank = topPromoEpisodeMap[ep.episode];
                const hasPass = ep.candidates.some((c) => c.verdict === "PASS");

                return (
                  <button
                    key={ep.episode}
                    onClick={() => onSelectEpisode(ep.episode)}
                    className={`h-9 rounded text-xs font-mono font-medium transition-all flex items-center justify-center relative cursor-pointer ${
                      isSelected
                        ? "bg-[#111111] text-white font-bold shadow-xs"
                        : topRank
                        ? "bg-amber-100 text-amber-950 border border-amber-300 font-bold hover:bg-amber-200"
                        : hasPass
                        ? "bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111]"
                        : "bg-[#e5e5e5] text-[#707072] border border-transparent"
                    }`}
                    title={`Episode ${ep.episode}${topRank ? ` (Ranked #${topRank})` : ""}`}
                  >
                    <span>{ep.episode < 10 ? `0${ep.episode}` : ep.episode}</span>
                    {topRank && (
                      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-amber-600 ring-1 ring-white"></span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-4 pt-3 border-t border-[#cacacb] flex items-center justify-between text-[11px] text-[#707072]">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-600"></span> Top 15 Ranked
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#111111]"></span> Passing Promo
              </span>
            </div>
          </div>
        </div>

        {/* Right Details Stage (3 cols) */}
        <div className="lg:col-span-3 space-y-6">
          {selectedEpisode && (
            <>
              {/* Episode Header Block with Distinct Border & Reduced Empty Space */}
              <div className="bg-[#f5f5f5] p-4 sm:p-5 border-2 border-[#cacacb] shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#cacacb]/60">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#707072]">
                        SERIES 01
                      </span>
                      {topPromoEpisodeMap[selectedEpisode.episode] && (
                        <span className="bg-amber-100 text-amber-950 border border-amber-300 text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-2xs">
                          🏆 Top 15 (Rank #{topPromoEpisodeMap[selectedEpisode.episode]})
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <h3 className="font-display text-3xl sm:text-4xl uppercase tracking-tight text-[#111111] font-bold">
                        EPISODE
                      </h3>
                      {/* Warm Number Box for Episode */}
                      <span className="bg-amber-100 text-amber-950 border border-amber-300 px-3.5 py-0.5 rounded font-mono font-bold text-3xl shadow-xs">
                        {selectedEpisode.episode < 10 ? `0${selectedEpisode.episode}` : selectedEpisode.episode}
                      </span>
                    </div>
                  </div>

                  <div className="text-left sm:text-right font-mono text-xs text-[#707072] space-y-1">
                    <p>Total Beats: <strong className="text-[#111111]">{selectedEpisode.total_beats}</strong></p>
                    <p>Candidates: <strong className="text-[#111111]">{selectedEpisode.candidates.length}</strong></p>
                  </div>
                </div>

                <div className="pt-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block mb-0.5">
                    Dramatic Logline
                  </span>
                  <p className="text-sm font-serif italic text-[#111111]">
                    &ldquo;{selectedEpisode.logline}&rdquo;
                  </p>
                </div>
              </div>

              {/* Candidates Grid with Distinct Borders */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#111111]">
                  Discovered Candidate Clips ({selectedEpisode.candidates.length})
                </h4>

                <div className="grid grid-cols-1 gap-5">
                  {selectedEpisode.candidates.map((cand, cIdx) => {
                    const isPass = cand.verdict === "PASS";
                    const copyKey = `${cand.episode}-${cand.start_formatted}`;
                    const isCopied = copiedKey === copyKey;
                    const fire = getFireRating(cand.composite_score || 8.0);
                    const isCandMatch = searchQuery.trim() ? matchesPromo(cand, searchQuery) : false;

                    return (
                      <div
                        key={cand.clip_id || cIdx}
                        className={`bg-white border-2 p-4 sm:p-5 space-y-3.5 shadow-xs transition-colors ${
                          isCandMatch
                            ? "border-amber-400 bg-amber-50/20"
                            : "border-[#cacacb] hover:border-[#111111]"
                        }`}
                      >
                        {/* Top row: Status, Warm Number Box, timestamps, score */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#e5e5e5]">
                          <div className="flex items-center gap-2.5 flex-wrap">
                            {/* Warm Candidate Number Box */}
                            <span className="bg-amber-50 text-amber-950 border border-amber-200/90 px-2.5 py-1 rounded text-xs font-mono font-bold">
                              Candidate #{cIdx + 1}
                            </span>

                            <span
                              className={`h-7 px-3 rounded-full text-xs font-semibold flex items-center gap-1 ${
                                isPass
                                  ? "bg-[#111111] text-white"
                                  : "bg-[#f5f5f5] text-[#707072] border border-[#cacacb]"
                              }`}
                            >
                              {isPass ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                              {cand.verdict}
                            </span>

                            {isCandMatch && (
                              <span className="bg-amber-100 text-amber-950 border border-amber-300 px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1 shadow-2xs">
                                <Target className="w-3 h-3 text-amber-800" /> Matches Search
                              </span>
                            )}

                            <span className="font-mono text-base font-bold text-[#111111]">
                              {cand.start_formatted} &ndash; {cand.end_formatted}
                            </span>

                            <span className="font-mono text-xs font-semibold text-[#111111] bg-[#f5f5f5] px-2.5 py-0.5 rounded-full border border-[#cacacb]">
                              {cand.duration.toFixed(1)}s
                            </span>
                          </div>

                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => handleCopy(cand)}
                              className="h-8 px-3.5 bg-[#f5f5f5] text-[#111111] rounded-full text-xs font-medium hover:bg-[#e5e5e5] active:scale-95 transition-all flex items-center gap-1.5 cursor-pointer border border-[#cacacb]/70"
                            >
                              {isCopied ? <Check className="w-3.5 h-3.5 text-[#007d48]" /> : <Copy className="w-3.5 h-3.5" />}
                              <span>{isCopied ? "Copied" : "Copy"}</span>
                            </button>
                          </div>
                        </div>

                        {/* Bold Rating Section with Fire Emojis */}
                        {cand.composite_score !== undefined && (
                          <div className="flex items-center justify-between gap-2 flex-wrap bg-[#f5f5f5]/60 p-2.5 border border-[#e5e5e5]">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold uppercase tracking-wider text-[#111111]">
                                Rating:
                              </span>
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded border font-mono font-extrabold text-xs shadow-2xs ${fire.badgeBg}`}>
                                <span>{fire.emojis}</span>
                                <span>{cand.composite_score.toFixed(1)} / 10</span>
                              </span>
                              <span className={`text-[11px] font-bold uppercase tracking-wide ${fire.tagColor}`}>
                                {fire.label}
                              </span>
                            </div>

                            <div className="flex items-center gap-3 text-[11px] font-mono text-[#707072]">
                              <span>Hook: <strong className="text-[#111111]">{cand.hook_score?.toFixed(1) || "N/A"}</strong></span>
                              <span>Cliffhanger: <strong className="text-[#111111]">{cand.cliffhanger_score?.toFixed(1) || "N/A"}</strong></span>
                              <span>Zero-Lore: <strong className="text-[#111111]">{cand.standalone_score?.toFixed(1) || "N/A"}</strong></span>
                            </div>
                          </div>
                        )}

                        {/* Partitioning Divider */}
                        <div className="border-t border-[#e5e5e5] my-1" />

                        {/* Safe Excerpts: Strictly <= 8 Words */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div className="bg-[#f5f5f5] p-3 border-l-2 border-[#111111] border-y border-r border-[#e5e5e5]">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block mb-1">
                              🪝 Hook Beat ({cand.hook_beat_id || "Beat"})
                            </span>
                            <p className="text-xs font-serif italic text-[#111111]">
                              &ldquo;{cand.hook_text_safe}&rdquo;
                            </p>
                          </div>

                          <div className="bg-[#f5f5f5] p-3 border-l-2 border-[#111111] border-y border-r border-[#e5e5e5]">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block mb-1">
                              ⚡ Cliffhanger Beat ({cand.cliffhanger_beat_id || "Beat"})
                            </span>
                            <p className="text-xs font-serif italic text-[#111111]">
                              &ldquo;{cand.cliffhanger_text_safe}&rdquo;
                            </p>
                          </div>
                        </div>

                        {/* Partitioning Divider before Description/Rationale */}
                        <div className="border-t border-[#e5e5e5] my-1" />

                        {/* Clean Partitioned Description / Conversion Rationale & Repairs */}
                        <div className="space-y-2 text-xs">
                          {cand.rationale && (
                            <div className="bg-[#f5f5f5] p-3 border border-[#e5e5e5] space-y-1">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block">
                                Why It Converts &middot; Rationale
                              </span>
                              <p className="text-[#39393b] leading-relaxed">
                                {cand.rationale}
                              </p>
                            </div>
                          )}

                          {cand.repairs && cand.repairs.length > 0 && (
                            <p className="text-[#707072] font-mono text-[11px] bg-[#f5f5f5] px-3 py-1.5 border border-[#e5e5e5]">
                              <strong>Pipeline Repairs Applied:</strong> {cand.repairs.join("; ")}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {!selectedEpisode && (
            <div className="bg-[#f5f5f5] p-12 text-center border-2 border-[#cacacb] space-y-4 shadow-xs">
              <h3 className="text-xl font-bold text-[#111111]">
                No episodes matched &ldquo;{searchQuery}&rdquo;
              </h3>
              <p className="text-sm text-[#707072] max-w-md mx-auto">
                No episode in the 50-episode catalog matched your query. Try searching by episode number (e.g. &ldquo;3&rdquo;, &ldquo;45&rdquo;), character name (&ldquo;Juliana&rdquo;, &ldquo;Alexander&rdquo;), or dramatic dialogue excerpt.
              </p>
              {onClearSearch && (
                <button
                  onClick={onClearSearch}
                  className="h-10 px-6 bg-[#111111] text-white rounded-full text-xs font-semibold hover:bg-neutral-800 transition-all cursor-pointer"
                >
                  Clear Search Filter
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
