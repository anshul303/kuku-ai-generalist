"use client";

import React, { useState } from "react";
import datasetData from "@/public/data/dataset.json";
import { DatasetPayload } from "./types";
import { Header } from "./components/Header";
import { CampaignHero } from "./components/CampaignHero";
import { SubNav } from "./components/SubNav";
import { RankedPromos } from "./components/RankedPromos";
import { EpisodeBrowser } from "./components/EpisodeBrowser";
import { StabilityView } from "./components/StabilityView";
import { FailuresView } from "./components/FailuresView";
import { SandboxRunner } from "./components/SandboxRunner";
import { Footer } from "./components/Footer";

export default function Home() {
  const dataset = datasetData as unknown as DatasetPayload;
  const [activeTab, setActiveTab] = useState<"ranked" | "episodes" | "stability" | "failures" | "sandbox">("ranked");
  const [selectedEpisodeNum, setSelectedEpisodeNum] = useState<number>(45);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [durationFilter, setDurationFilter] = useState<"all" | "short" | "medium" | "long">("all");
  const [sortBy, setSortBy] = useState<"rank" | "score" | "duration">("rank");
  const [showFilters, setShowFilters] = useState<boolean>(true);

  // Build topPromoEpisodeMap
  const topPromoEpisodeMap: Record<number, number> = {};
  dataset.top15.forEach((p, idx) => {
    if (!topPromoEpisodeMap[p.episode]) {
      topPromoEpisodeMap[p.episode] = p.rank || idx + 1;
    }
  });

  const handleSelectEpisode = (epNum: number) => {
    setSelectedEpisodeNum(epNum);
    setActiveTab("episodes");
    window.scrollTo({ top: 400, behavior: "smooth" });
  };

  const handleSearchChange = (q: string) => {
    setSearchQuery(q);
    // If user begins searching while in meta tabs, auto-switch to ranked promos to reveal matches
    if (q.trim() && (activeTab === "stability" || activeTab === "failures" || activeTab === "sandbox")) {
      setActiveTab("ranked");
    }
  };

  const handleClearSearch = () => {
    setSearchQuery("");
  };

  return (
    <div className="min-h-screen flex flex-col bg-white text-[#111111]">
      {/* 1. Nike Top Navigation (Utility Bar + Primary Nav + Confidentiality Strip) */}
      <Header
        meta={dataset.meta}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
      />

      {/* 2. Editorial Campaign Hero (Towering Display Headline + On-Image Pill CTA) */}
      {activeTab === "ranked" && !searchQuery && (
        <CampaignHero
          onExploreTop={() => {
            const el = document.getElementById("ranked-section");
            el?.scrollIntoView({ behavior: "smooth" });
          }}
          onBrowseAll={() => {
            setActiveTab("episodes");
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        />
      )}

      {/* 3. Sub-Nav Strip (Breadcrumb, Duration Filter Chips, Sort Control) */}
      <SubNav
        itemCount={activeTab === "ranked" ? dataset.top15.length : dataset.episodes.length}
        durationFilter={durationFilter}
        onDurationFilterChange={setDurationFilter}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        showFilters={showFilters}
        onToggleFilters={() => setShowFilters(!showFilters)}
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        activeTab={activeTab}
      />

      {/* 4. Main Content Area (Max width 1440px with responsive edge gutters) */}
      <main id="ranked-section" className="flex-1 max-w-[1440px] w-full mx-auto px-6 sm:px-8">
        {activeTab === "ranked" && (
          <RankedPromos
            topPromos={dataset.top15}
            onSelectEpisode={handleSelectEpisode}
            searchQuery={searchQuery}
            durationFilter={durationFilter}
            sortBy={sortBy}
            allEpisodes={dataset.episodes}
            onClearSearch={handleClearSearch}
          />
        )}

        {activeTab === "episodes" && (
          <EpisodeBrowser
            episodes={dataset.episodes}
            selectedEpisodeNum={selectedEpisodeNum}
            onSelectEpisode={setSelectedEpisodeNum}
            topPromoEpisodeMap={topPromoEpisodeMap}
            searchQuery={searchQuery}
            onSearchChange={handleSearchChange}
            onClearSearch={handleClearSearch}
          />
        )}

        {activeTab === "stability" && <StabilityView meta={dataset.meta} />}

        {activeTab === "failures" && <FailuresView />}

        {activeTab === "sandbox" && <SandboxRunner />}
      </main>

      {/* 5. Authentic Nike 4-Column Footer */}
      <Footer />
    </div>
  );
}
