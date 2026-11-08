"use client";

import React from "react";
import { SlidersHorizontal, ChevronDown, Search, X } from "lucide-react";

interface SubNavProps {
  itemCount: number;
  durationFilter: "all" | "short" | "medium" | "long";
  onDurationFilterChange: (val: "all" | "short" | "medium" | "long") => void;
  sortBy: "rank" | "score" | "duration";
  onSortByChange: (val: "rank" | "score" | "duration") => void;
  showFilters: boolean;
  onToggleFilters: () => void;
  searchQuery?: string;
  onSearchChange?: (val: string) => void;
  activeTab?: string;
}

export const SubNav: React.FC<SubNavProps> = ({
  itemCount,
  durationFilter,
  onDurationFilterChange,
  sortBy,
  onSortByChange,
  showFilters,
  onToggleFilters,
  searchQuery = "",
  onSearchChange,
  activeTab = "ranked",
}) => {
  return (
    <div className="w-full bg-white border-b border-[#cacacb]/60 mb-8 py-3.5">
      <div className="max-w-[1440px] mx-auto px-6 sm:px-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Breadcrumb + Item Count + Search Query Badge */}
        <div className="flex items-center gap-2 text-sm text-[#707072] flex-wrap">
          <span>Microdramas</span>
          <span>/</span>
          <span>I Married a Broken Soldier</span>
          <span>/</span>
          <span className="text-[#111111] font-bold">
            {activeTab === "ranked" ? "Top Promos" : "All Episodes"} ({itemCount})
          </span>

          {searchQuery && (
            <div className="flex items-center gap-1.5 ml-2 bg-amber-50 text-amber-950 px-2.5 py-0.5 rounded-full text-xs border border-amber-300 font-medium">
              <span>Search: &ldquo;{searchQuery}&rdquo;</span>
              {onSearchChange && (
                <button
                  onClick={() => onSearchChange("")}
                  className="hover:text-amber-700 cursor-pointer ml-0.5"
                  title="Clear search"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Filter Pills, Inline Search, and Sort Control */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Inline Search Field */}
          {onSearchChange && (
            <div className="relative flex items-center">
              <Search className="w-3.5 h-3.5 text-[#707072] absolute left-3 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Filter by quote, ep#, rank..."
                className="w-48 sm:w-56 h-9 bg-[#f5f5f5] text-[#111111] text-xs font-normal pl-8 pr-7 rounded-full border border-[#cacacb] focus:border-[#111111] focus:bg-white focus:outline-none transition-all placeholder:text-[#707072]"
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange("")}
                  className="absolute right-2 text-[#707072] hover:text-[#111111] cursor-pointer"
                  title="Clear search"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}

          {/* Filter Chips: 8px 16px, rounded-full, 1px hairline. Inverted when active! */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <button
              onClick={() => onDurationFilterChange("all")}
              className={`h-9 px-4 rounded-full text-[13px] font-medium transition-all cursor-pointer ${
                durationFilter === "all"
                  ? "bg-[#111111] text-white"
                  : "bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111]"
              }`}
            >
              All Promos
            </button>

            <button
              onClick={() => onDurationFilterChange("short")}
              className={`h-9 px-4 rounded-full text-[13px] font-medium transition-all cursor-pointer ${
                durationFilter === "short"
                  ? "bg-[#111111] text-white"
                  : "bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111]"
              }`}
            >
              Snappy (&le; 30s)
            </button>

            <button
              onClick={() => onDurationFilterChange("medium")}
              className={`h-9 px-4 rounded-full text-[13px] font-medium transition-all cursor-pointer ${
                durationFilter === "medium"
                  ? "bg-[#111111] text-white"
                  : "bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111]"
              }`}
            >
              Standard (31&ndash;45s)
            </button>

            <button
              onClick={() => onDurationFilterChange("long")}
              className={`h-9 px-4 rounded-full text-[13px] font-medium transition-all cursor-pointer ${
                durationFilter === "long"
                  ? "bg-[#111111] text-white"
                  : "bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111]"
              }`}
            >
              Deep Drama (46&ndash;60s)
            </button>
          </div>

          {/* Sort By Dropdown */}
          <div className="flex items-center gap-2 pl-2 border-l border-[#cacacb]">
            <span className="text-xs text-[#707072]">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => onSortByChange(e.target.value as any)}
              className="bg-transparent text-xs font-semibold text-[#111111] focus:outline-none cursor-pointer pr-1"
            >
              <option value="rank">Listwise Rank (Top #1 &rarr; #15)</option>
              <option value="score">Composite Score</option>
              <option value="duration">Clip Duration</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};
