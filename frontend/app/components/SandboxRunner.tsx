"use client";

import React, { useState } from "react";
import {
  Play,
  Upload,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  Download,
  FileText,
  Sliders,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { PromoCandidate } from "../types";

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

const SAMPLE_SCENE_A = `1
00:00:00,000 --> 00:00:03,200
[E01-B001]
The great cathedral doors burst open with a deafening crash as cold rain sweeps across the marble floor.

2
00:00:03,200 --> 00:00:07,500
[E01-B002]
VICTORIA:
(sneering cruel laughter)
Did you honestly believe the Duke of Ashburton would marry an impoverished, disgraced orphan like you?

3
00:00:07,500 --> 00:00:12,100
[E01-B003]
JULIANA:
(voice trembling but resolute)
The vows are signed before the bishop. This marriage is lawful!

4
00:00:12,100 --> 00:00:18,400
[E01-B004]
Victoria seizes the parchment and rips it into jagged shreds before Juliana's widening eyes.

5
00:00:18,400 --> 00:00:23,800
[E01-B005]
VICTORIA:
A piece of paper means nothing without an army. Guards, drag this beggar into the mud!

6
00:00:23,800 --> 00:00:28,200
[E01-B006]
Two armored sentries grab Juliana's wrists, forcing her onto her knees on the rain-slicked steps.

7
00:00:28,200 --> 00:00:34,500
[E01-B007]
HEAVY BOOTSTEPS ECHO SLOWLY.
A deep, gravelly voice cuts through the thunder like steel.

8
00:00:34,500 --> 00:00:40,000
[E01-B008]
ALEXANDER:
Unclench your hands from my wife this instant... or lose them.`;

export const SandboxRunner: React.FC = () => {
  // Input scope
  const [sourceMode, setSourceMode] = useState<"preloaded" | "uploaded" | "text">("preloaded");
  const [maxEpisodes, setMaxEpisodes] = useState<number>(50);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ filename: string; content: string }>>([]);
  const [scriptText, setScriptText] = useState<string>(SAMPLE_SCENE_A);

  // Provider configuration
  const [provider, setProvider] = useState<string>("mock");
  const [model, setModel] = useState<string>("mock");
  const [apiKey, setApiKey] = useState<string>("");
  const [baseUrl, setBaseUrl] = useState<string>("http://localhost:11434/v1");
  const [noCache, setNoCache] = useState<boolean>(false);

  // Execution state
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [results, setResults] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Results sub-view
  const [resultTab, setResultTab] = useState<"ranked" | "episodes">("ranked");
  const [inspectEpNum, setInspectEpNum] = useState<number>(1);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleProviderChange = (p: string) => {
    setProvider(p);
    if (p === "mock") setModel("mock");
    else if (p === "gemini") setModel("gemini-3.5-flash-lite");
    else if (p === "openai") setModel("gpt-4o-mini");
    else if (p === "anthropic") setModel("claude-3-5-haiku-latest");
    else if (p === "openai_compatible") setModel("llama3");
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const fileList: Array<{ filename: string; content: string }> = [];
    let loadedCount = 0;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        fileList.push({ filename: file.name, content });
        loadedCount += 1;
        if (loadedCount === files.length) {
          fileList.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true }));
          setUploadedFiles(fileList);
          setMaxEpisodes(fileList.length);
        }
      };
      reader.readAsText(file);
    });
  };

  const handleRun = async () => {
    setLoading(true);
    setErrorMsg(null);
    setResults(null);
    setStatusMessage("Initializing batch discovery engine...");

    try {
      let payload: any = {
        source: sourceMode,
        provider,
        model,
        api_key: apiKey,
        base_url: baseUrl,
        no_cache: noCache,
      };

      if (sourceMode === "preloaded") {
        payload.max_episodes = maxEpisodes;
        setStatusMessage(`Loading & parsing ${maxEpisodes} preloaded episodes...`);
      } else if (sourceMode === "uploaded") {
        if (uploadedFiles.length === 0) {
          throw new Error("Please select one or more .txt screenplay files to process.");
        }
        payload.files = uploadedFiles;
        payload.max_episodes = uploadedFiles.length;
        setStatusMessage(`Parsing batch of ${uploadedFiles.length} uploaded screenplay files...`);
      } else if (sourceMode === "text") {
        if (!scriptText.trim()) {
          throw new Error("Please provide screenplay text.");
        }
        payload.text = scriptText;
        setStatusMessage("Parsing custom screenplay text...");
      }

      setStatusMessage("Executing Batched Proposal & Cold Judging Pipeline...");

      const res = await fetch("/api/batch-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || data.stderr || "Batch promo discovery execution failed.");
      }

      setResults(data);
      if (data.episodes && data.episodes.length > 0) {
        setInspectEpNum(data.episodes[0].episode);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred during execution.");
    } finally {
      setLoading(false);
      setStatusMessage("");
    }
  };

  const handleCopy = (promo: PromoCandidate) => {
    const text = `Episode ${promo.episode}: ${promo.start_formatted} - ${promo.end_formatted} (${promo.duration}s)`;
    navigator.clipboard.writeText(text);
    setCopiedKey(`${promo.episode}-${promo.start_formatted}`);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleDownloadJSON = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `kuku_batch_run_${results.provider}_${results.total_episodes}eps.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const selectedEpResult = results?.episodes?.find((e: any) => e.episode === inspectEpNum) || results?.episodes?.[0];

  return (
    <section className="space-y-12">
      {/* Section Header: Nike 32px Heading-XL */}
      <div className="pb-2 border-b border-[#cacacb]/40">
        <h2 className="text-[28px] sm:text-[32px] font-medium uppercase tracking-tight text-[#111111]">
          RUN IT YOURSELF &middot; 50-EPISODE BATCH ENGINE
        </h2>
        <p className="text-sm text-[#707072] mt-1">
          Execute full promotional discovery across all 50 preloaded episodes, or batch-upload 1 to 50 custom screenplays (.txt) simultaneously.
        </p>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Step 1: Input Source & Scope */}
        <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#111111]">
            1. Screenplay Input Scope
          </h3>

          <div className="space-y-3 text-xs">
            {/* Scope Selector Options */}
            <div className="space-y-2">
              <label
                onClick={() => setSourceMode("preloaded")}
                className={`flex items-start gap-3 p-3 border rounded-none cursor-pointer transition-all ${
                  sourceMode === "preloaded"
                    ? "bg-white border-[#111111]"
                    : "bg-[#f5f5f5] border-[#cacacb] hover:bg-white/60"
                }`}
              >
                <input
                  type="radio"
                  name="sourceMode"
                  checked={sourceMode === "preloaded"}
                  onChange={() => setSourceMode("preloaded")}
                  className="mt-0.5 accent-[#111111]"
                />
                <div>
                  <span className="font-bold text-[#111111] block">Preloaded 50-Episode Series</span>
                  <span className="text-[11px] text-[#707072]">
                    *I Married a Broken Soldier. He was a Duke* (All 50 episodes in assets/)
                  </span>
                </div>
              </label>

              <label
                onClick={() => setSourceMode("uploaded")}
                className={`flex items-start gap-3 p-3 border rounded-none cursor-pointer transition-all ${
                  sourceMode === "uploaded"
                    ? "bg-white border-[#111111]"
                    : "bg-[#f5f5f5] border-[#cacacb] hover:bg-white/60"
                }`}
              >
                <input
                  type="radio"
                  name="sourceMode"
                  checked={sourceMode === "uploaded"}
                  onChange={() => setSourceMode("uploaded")}
                  className="mt-0.5 accent-[#111111]"
                />
                <div>
                  <span className="font-bold text-[#111111] block">Upload Multi-File Batch (.txt)</span>
                  <span className="text-[11px] text-[#707072]">
                    Select multiple files at once (1 to 50+ screenplay text files)
                  </span>
                </div>
              </label>

              <label
                onClick={() => setSourceMode("text")}
                className={`flex items-start gap-3 p-3 border rounded-none cursor-pointer transition-all ${
                  sourceMode === "text"
                    ? "bg-white border-[#111111]"
                    : "bg-[#f5f5f5] border-[#cacacb] hover:bg-white/60"
                }`}
              >
                <input
                  type="radio"
                  name="sourceMode"
                  checked={sourceMode === "text"}
                  onChange={() => setSourceMode("text")}
                  className="mt-0.5 accent-[#111111]"
                />
                <div>
                  <span className="font-bold text-[#111111] block">Paste Single Screenplay Scene</span>
                  <span className="text-[11px] text-[#707072]">Direct text testing for a single scene</span>
                </div>
              </label>
            </div>

            {/* Scope-specific controls */}
            {sourceMode === "preloaded" && (
              <div className="pt-3 border-t border-[#cacacb]/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#707072]">
                    Episodes to Process:
                  </span>
                  <span className="font-mono font-bold text-[#111111]">{maxEpisodes} Episodes</span>
                </div>

                <div className="flex items-center gap-1.5 pt-1">
                  <button
                    onClick={() => setMaxEpisodes(50)}
                    className={`h-8 px-3 rounded-full text-[11px] font-medium transition-all ${
                      maxEpisodes === 50
                        ? "bg-[#111111] text-white"
                        : "bg-white text-[#111111] border border-[#cacacb]"
                    }`}
                  >
                    All 50 Eps
                  </button>
                  <button
                    onClick={() => setMaxEpisodes(20)}
                    className={`h-8 px-3 rounded-full text-[11px] font-medium transition-all ${
                      maxEpisodes === 20
                        ? "bg-[#111111] text-white"
                        : "bg-white text-[#111111] border border-[#cacacb]"
                    }`}
                  >
                    20 Eps
                  </button>
                  <button
                    onClick={() => setMaxEpisodes(10)}
                    className={`h-8 px-3 rounded-full text-[11px] font-medium transition-all ${
                      maxEpisodes === 10
                        ? "bg-[#111111] text-white"
                        : "bg-white text-[#111111] border border-[#cacacb]"
                    }`}
                  >
                    10 Eps
                  </button>
                  <button
                    onClick={() => setMaxEpisodes(5)}
                    className={`h-8 px-3 rounded-full text-[11px] font-medium transition-all ${
                      maxEpisodes === 5
                        ? "bg-[#111111] text-white"
                        : "bg-white text-[#111111] border border-[#cacacb]"
                    }`}
                  >
                    Smoke Test (5)
                  </button>
                </div>
              </div>
            )}

            {sourceMode === "uploaded" && (
              <div className="pt-3 border-t border-[#cacacb]/60 space-y-3">
                <label className="h-12 w-full bg-white text-[#111111] rounded-full border-2 border-dashed border-[#cacacb] hover:border-[#111111] text-xs font-medium flex items-center justify-center gap-2 cursor-pointer transition-all">
                  <Upload className="w-4 h-4" /> Select Multi-Screenplay Files (.txt)
                  <input
                    type="file"
                    multiple
                    accept=".txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>

                {uploadedFiles.length > 0 && (
                  <div className="bg-white p-3 border border-[#cacacb] space-y-1 font-mono text-[11px]">
                    <span className="font-bold text-[#007d48] flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> {uploadedFiles.length} Screenplay Files Loaded
                    </span>
                    <p className="text-[#707072] truncate">
                      {uploadedFiles.map((f) => f.filename).slice(0, 3).join(", ")}
                      {uploadedFiles.length > 3 ? ` ... and ${uploadedFiles.length - 3} more` : ""}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Provider & Credentials */}
        <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#111111]">
            2. Inference Provider &amp; Model
          </h3>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-[#707072] mb-1 font-medium">Provider</label>
              <select
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="w-full h-11 bg-white border border-[#cacacb] rounded-full px-4 text-[#111111] font-medium focus:outline-none focus:border-[#111111] cursor-pointer"
              >
                <option value="mock">Offline Mock Rule Engine (Zero Quota &middot; Fast)</option>
                <option value="gemini">Google Gemini (gemini-3.5-flash-lite)</option>
                <option value="openai">OpenAI (gpt-4o-mini)</option>
                <option value="anthropic">Anthropic (claude-3-5-haiku-latest)</option>
                <option value="openai_compatible">OpenAI-Compatible (Ollama, vLLM, Groq)</option>
              </select>
            </div>

            {provider === "openai_compatible" && (
              <>
                <div>
                  <label className="block text-[#707072] mb-1 font-medium">Base URL</label>
                  <input
                    type="text"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="http://localhost:11434/v1"
                    className="w-full h-11 bg-white border border-[#cacacb] rounded-full px-4 text-[#111111] font-mono focus:outline-none focus:border-[#111111]"
                  />
                </div>

                <div>
                  <label className="block text-[#707072] mb-1 font-medium">Model Name</label>
                  <input
                    type="text"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    placeholder="llama3"
                    className="w-full h-11 bg-white border border-[#cacacb] rounded-full px-4 text-[#111111] font-mono focus:outline-none focus:border-[#111111]"
                  />
                </div>
              </>
            )}

            {provider !== "mock" && (
              <div>
                <label className="block text-[#707072] mb-1 font-medium">API Key (Optional if in .env)</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Paste custom API key or leave blank"
                  className="w-full h-11 bg-white border border-[#cacacb] rounded-full px-4 text-[#111111] font-mono focus:outline-none focus:border-[#111111]"
                />
              </div>
            )}

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="bypassCache"
                checked={noCache}
                onChange={(e) => setNoCache(e.target.checked)}
                className="accent-[#111111] h-4 w-4"
              />
              <label htmlFor="bypassCache" className="text-[11px] text-[#707072] cursor-pointer">
                Bypass disk cache (<code className="font-mono text-[#111111]">--no-cache</code>)
              </label>
            </div>
          </div>
        </div>

        {/* Step 3: Trigger & Batch Strategy */}
        <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#111111]">
              3. Batch Execution Strategy
            </h3>

            <div className="bg-white p-4 border border-[#cacacb] text-xs space-y-2">
              <p className="flex justify-between text-[#707072]">
                <span>Target Episodes:</span>
                <strong className="text-[#111111] font-mono">
                  {sourceMode === "preloaded"
                    ? `${maxEpisodes} Episodes`
                    : sourceMode === "uploaded"
                    ? `${uploadedFiles.length} Uploaded Files`
                    : "1 Custom Scene"}
                </strong>
              </p>
              <p className="flex justify-between text-[#707072]">
                <span>Propose Batching:</span>
                <strong className="text-[#111111] font-mono">~10 Eps / Call</strong>
              </p>
              <p className="flex justify-between text-[#707072]">
                <span>Judge Batching:</span>
                <strong className="text-[#111111] font-mono">~30 Clips / Call</strong>
              </p>
              <p className="flex justify-between text-[#707072]">
                <span>Ranking:</span>
                <strong className="text-[#111111] font-mono">1 Global Listwise Call</strong>
              </p>
              <p className="flex justify-between text-[#707072] pt-2 border-t border-[#f5f5f5]">
                <span>Free-Tier Quota Target:</span>
                <strong className="text-[#007d48] font-mono">&le; 10 Calls Total</strong>
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {/* button-primary: Nike black pill, 48px height, rounded-full */}
            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full h-12 bg-[#111111] text-white rounded-full text-sm font-medium hover:bg-neutral-800 active:scale-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer shadow-none"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> {statusMessage || "Processing Batch..."}
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  Run Batch Discovery ({sourceMode === "preloaded" ? maxEpisodes : sourceMode === "uploaded" ? uploadedFiles.length : 1} Eps)
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Screenplay text editor (for text mode) */}
      {sourceMode === "text" && (
        <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[#111111]">
              Screenplay Text (Paste / Edit)
            </span>
            <button
              onClick={() => setScriptText(SAMPLE_SCENE_A)}
              className="h-8 px-3 bg-white text-[#111111] border border-[#cacacb] rounded-full text-xs font-medium cursor-pointer"
            >
              Reset Sample Scene
            </button>
          </div>
          <textarea
            value={scriptText}
            onChange={(e) => setScriptText(e.target.value)}
            rows={10}
            className="w-full bg-white border border-[#cacacb] p-4 font-mono text-xs text-[#111111] focus:outline-none focus:border-[#111111] leading-relaxed resize-y"
          />
        </div>
      )}

      {/* Error Notice */}
      {errorMsg && (
        <div className="bg-white border-2 border-[#d30005] p-5 text-xs text-[#d30005] flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p><strong>Execution Error:</strong> {errorMsg}</p>
        </div>
      )}

      {/* Batch Results View */}
      {results && (
        <div className="space-y-8 pt-8 border-t border-[#cacacb]">
          {/* Summary Telemetry Bar */}
          <div className="bg-[#f5f5f5] p-6 border border-[#cacacb]/60 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="bg-[#111111] text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase">
                  Batch Run Succeeded
                </span>
                <span className="text-xs font-mono text-[#707072]">
                  {results.provider} &middot; {results.model}
                </span>
              </div>
              <h3 className="font-display text-3xl sm:text-4xl uppercase tracking-tight text-[#111111] font-normal mt-1">
                {results.total_episodes} EPISODES PROCESSED &middot; {results.total_candidates} CANDIDATES FOUND
              </h3>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="bg-white border border-[#cacacb] px-4 py-2 text-center text-xs">
                <span className="text-[10px] uppercase font-bold text-[#707072] block">Runtime</span>
                <span className="font-mono font-bold text-[#111111]">{results.runtime_seconds}s</span>
              </div>

              <div className="bg-white border border-[#cacacb] px-4 py-2 text-center text-xs">
                <span className="text-[10px] uppercase font-bold text-[#707072] block">API Calls</span>
                <span className="font-mono font-bold text-[#111111]">{results.total_calls} Calls</span>
              </div>

              <div className="bg-white border border-[#cacacb] px-4 py-2 text-center text-xs">
                <span className="text-[10px] uppercase font-bold text-[#707072] block">Free Tier Cost</span>
                <span className="font-mono font-bold text-[#007d48]">$0.00</span>
              </div>

              <button
                onClick={handleDownloadJSON}
                className="h-11 px-6 bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111] rounded-full text-xs font-medium active:scale-95 transition-all flex items-center gap-2 cursor-pointer"
              >
                <Download className="w-4 h-4" /> Download Batch JSON
              </button>
            </div>
          </div>

          {/* Sub-view toggle (Top Ranked vs All Episodes) */}
          <div className="flex items-center gap-2 border-b border-[#cacacb]">
            <button
              onClick={() => setResultTab("ranked")}
              className={`h-11 px-5 text-sm font-medium tracking-tight relative cursor-pointer ${
                resultTab === "ranked"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              Top Ranked Promos ({results.top_ranked?.length || 0})
            </button>

            <button
              onClick={() => setResultTab("episodes")}
              className={`h-11 px-5 text-sm font-medium tracking-tight relative cursor-pointer ${
                resultTab === "episodes"
                  ? "text-[#111111] font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-[#111111]"
                  : "text-[#707072] hover:text-[#111111]"
              }`}
            >
              Episode Breakdown ({results.episodes?.length || 0})
            </button>
          </div>

          {/* Sub-view 1: Top Ranked Promos from the Batch */}
          {resultTab === "ranked" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.top_ranked?.map((promo: any, idx: number) => {
                const rank = promo.rank || idx + 1;
                const copyKey = `${promo.episode}-${promo.start_formatted}`;
                const isCopied = copiedKey === copyKey;
                const fire = getFireRating(promo.composite_score || 8.5);

                let rankNumberBox = (
                  <span className="bg-[#f5f5f5] text-[#111111] border border-[#cacacb] text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full uppercase">
                    Rank #{rank}
                  </span>
                );
                let episodeNumberBox = (
                  <span className="bg-[#e5e5e5] text-[#111111] border border-[#cacacb] font-mono font-bold px-2 py-0.5 rounded text-lg">
                    {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
                  </span>
                );
                let cardBorderClass = "border border-[#cacacb] hover:border-[#111111]";

                if (rank === 1) {
                  rankNumberBox = (
                    <span className="bg-gradient-to-br from-amber-500 via-amber-600 to-orange-500 text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-xs flex items-center gap-1 uppercase">
                      <Sparkles className="w-3 h-3 text-amber-100" /> #1 Ranked
                    </span>
                  );
                  episodeNumberBox = (
                    <span className="bg-amber-100 text-amber-950 border border-amber-300 font-mono font-bold px-2 py-0.5 rounded text-lg shadow-2xs">
                      {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
                    </span>
                  );
                  cardBorderClass = "border-2 border-amber-400/80 hover:border-amber-500 shadow-sm";
                } else if (rank === 2) {
                  rankNumberBox = (
                    <span className="bg-gradient-to-br from-orange-400 via-rose-400 to-amber-500 text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-xs flex items-center gap-1 uppercase">
                      <Sparkles className="w-3 h-3 text-orange-100" /> #2 Ranked
                    </span>
                  );
                  episodeNumberBox = (
                    <span className="bg-orange-100 text-orange-950 border border-orange-300 font-mono font-bold px-2 py-0.5 rounded text-lg shadow-2xs">
                      {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
                    </span>
                  );
                  cardBorderClass = "border-2 border-orange-300/80 hover:border-orange-400 shadow-sm";
                } else if (rank === 3) {
                  rankNumberBox = (
                    <span className="bg-gradient-to-br from-amber-600 to-yellow-600 text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full shadow-xs flex items-center gap-1 uppercase">
                      <Sparkles className="w-3 h-3 text-amber-100" /> #3 Ranked
                    </span>
                  );
                  episodeNumberBox = (
                    <span className="bg-yellow-100 text-yellow-950 border border-yellow-300 font-mono font-bold px-2 py-0.5 rounded text-lg shadow-2xs">
                      {promo.episode < 10 ? `0${promo.episode}` : promo.episode}
                    </span>
                  );
                  cardBorderClass = "border-2 border-yellow-400/70 hover:border-yellow-500 shadow-sm";
                }

                return (
                  <div
                    key={promo.clip_id || idx}
                    className={`bg-white p-4 sm:p-5 flex flex-col justify-between transition-all ${cardBorderClass}`}
                  >
                    <div>
                      {/* Compact aspect stage on #f5f5f5 (Reduced dead empty space) */}
                      <div className="w-full aspect-[16/10] bg-[#f5f5f5] p-3 flex flex-col justify-between border border-[#e5e5e5] mb-3">
                        <div className="flex items-center justify-between">
                          {rankNumberBox}
                          <span className="font-mono text-xs text-[#707072] bg-white px-2 py-0.5 rounded-full border border-[#cacacb]/50">
                            {promo.duration?.toFixed(1)}s Runtime
                          </span>
                        </div>

                        <div className="text-center my-auto">
                          <div className="inline-flex items-center gap-2 mb-1">
                            <span className="text-xs font-bold uppercase tracking-widest text-[#707072]">
                              EPISODE
                            </span>
                            {episodeNumberBox}
                          </div>
                          <p className="font-mono text-xs font-bold text-[#111111]">
                            {promo.start_formatted} &ndash; {promo.end_formatted}
                          </p>
                        </div>

                        <div className="flex justify-between text-[10px] text-[#707072] font-mono">
                          <span>Hook: <strong>{promo.hook_score?.toFixed(1) || 8.5}</strong></span>
                          <span>Cut: <strong>{promo.end_formatted}</strong></span>
                        </div>
                      </div>

                      {/* Bold Episode Title */}
                      <div className="flex items-baseline justify-between gap-2 pb-2">
                        <h4 className="text-base sm:text-lg font-bold text-[#111111] tracking-tight">
                          Episode {promo.episode}
                        </h4>
                        <span className="text-xs font-mono font-semibold text-[#707072]">
                          {promo.start_formatted} &ndash; {promo.end_formatted}
                        </span>
                      </div>

                      {/* Partitioning Divider */}
                      <div className="border-t border-[#e5e5e5] mb-2.5" />

                      {/* Bold Rating Section with Fire Emojis */}
                      <div className="flex items-center justify-between gap-2 pb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase text-[#111111]">
                            Rating:
                          </span>
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded border font-mono font-extrabold text-xs shadow-2xs ${fire.badgeBg}`}>
                            <span>{fire.emojis}</span>
                            <span>{(promo.composite_score || 8.5).toFixed(1)} / 10</span>
                          </span>
                        </div>
                        <span className={`text-[11px] font-bold uppercase tracking-wide ${fire.tagColor}`}>
                          {fire.label}
                        </span>
                      </div>

                      {/* Partitioning Divider */}
                      <div className="border-t border-[#e5e5e5] mb-2.5" />

                      {/* Safe Dialogue Excerpts Block */}
                      <div className="space-y-2 bg-[#f5f5f5]/80 p-2.5 border border-[#e5e5e5] text-xs">
                        <div>
                          <span className="text-[10px] uppercase font-bold tracking-wider text-[#707072] block mb-0.5">
                            🪝 0–3s Hook Excerpt
                          </span>
                          <p className="font-serif italic text-[#111111] line-clamp-1">
                            &ldquo;{promo.hook_text_safe}&rdquo;
                          </p>
                        </div>

                        <div className="border-t border-[#e5e5e5] pt-1.5">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-[#707072] block mb-0.5">
                            ⚡ Cliffhanger Cutpoint
                          </span>
                          <p className="font-serif italic text-[#111111] line-clamp-1">
                            &ldquo;{promo.cliffhanger_text_safe}&rdquo;
                          </p>
                        </div>
                      </div>

                      {/* Partitioning Divider */}
                      <div className="border-t border-[#e5e5e5] my-2.5" />

                      {/* Description / Conversion Rationale */}
                      {promo.rationale && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#707072] block">
                            Why It Converts &middot; Rationale
                          </span>
                          <p className="text-[#39393b] text-xs leading-relaxed line-clamp-2">
                            {promo.rationale}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="pt-3.5 mt-3 border-t border-[#cacacb]/60">
                      <button
                        onClick={() => handleCopy(promo)}
                        className="w-full h-10 bg-[#f5f5f5] text-[#111111] hover:bg-[#e5e5e5] rounded-full text-xs font-medium active:scale-95 transition-all flex items-center justify-center gap-1.5 cursor-pointer border border-[#cacacb]/70"
                      >
                        {isCopied ? <Check className="w-3.5 h-3.5 text-[#007d48]" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{isCopied ? "Copied Range" : "Copy Timestamps"}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Sub-view 2: Full Episode Breakdown */}
          {resultTab === "episodes" && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Left Episode Selector */}
              <div className="lg:col-span-1 bg-[#f5f5f5] p-4 border border-[#cacacb]/60">
                <span className="text-xs font-bold uppercase tracking-wider text-[#111111] block mb-3">
                  Episodes in Batch ({results.episodes?.length || 0})
                </span>

                <div className="grid grid-cols-5 gap-1.5 max-h-[440px] overflow-y-auto pr-1">
                  {results.episodes?.map((ep: any) => {
                    const isSelected = ep.episode === inspectEpNum;
                    const hasPass = ep.candidates?.some((c: any) => c.verdict === "PASS");

                    return (
                      <button
                        key={ep.episode}
                        onClick={() => setInspectEpNum(ep.episode)}
                        className={`h-9 rounded-full text-xs font-mono font-medium transition-all flex items-center justify-center cursor-pointer ${
                          isSelected
                            ? "bg-[#111111] text-white"
                            : hasPass
                            ? "bg-white text-[#111111] border border-[#cacacb] hover:border-[#111111]"
                            : "bg-[#e5e5e5] text-[#707072]"
                        }`}
                      >
                        {ep.episode < 10 ? `0${ep.episode}` : ep.episode}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Right Candidates Inspector */}
              <div className="lg:col-span-3 space-y-4">
                {selectedEpResult && (
                  <div className="space-y-4">
                    <div className="bg-[#f5f5f5] p-4 sm:p-5 border border-[#cacacb]/60">
                      <div className="flex items-center justify-between pb-3 border-b border-[#cacacb]/60">
                        <h4 className="font-display text-3xl uppercase text-[#111111] font-bold">
                          EPISODE {selectedEpResult.episode}
                        </h4>
                        <span className="font-mono text-xs text-[#707072]">
                          Total Beats: <strong className="text-[#111111]">{selectedEpResult.total_beats}</strong> &middot; Candidates: <strong className="text-[#111111]">{selectedEpResult.candidates?.length || 0}</strong>
                        </span>
                      </div>
                      <p className="text-xs font-serif italic text-[#111111] mt-2">
                        &ldquo;{selectedEpResult.logline}&rdquo;
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                      {selectedEpResult.candidates?.map((cand: any, cIdx: number) => {
                        const isPass = cand.verdict === "PASS";
                        const copyKey = `${cand.episode}-${cand.start_formatted}`;
                        const isCopied = copiedKey === copyKey;
                        const fire = getFireRating(cand.composite_score || 8.0);

                        return (
                          <div
                            key={cand.clip_id || cIdx}
                            className="bg-white border-2 border-[#cacacb] hover:border-[#111111] p-4 sm:p-5 space-y-3 text-xs transition-colors"
                          >
                            <div className="flex items-center justify-between pb-2 border-b border-[#e5e5e5]">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="bg-[#111111] text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full">
                                  {cand.verdict}
                                </span>
                                <span className="font-mono font-bold text-sm text-[#111111]">
                                  {cand.start_formatted} &ndash; {cand.end_formatted}
                                </span>
                                <span className="font-mono text-xs font-semibold text-[#707072] bg-[#f5f5f5] px-2 py-0.5 rounded-full border border-[#cacacb]">
                                  {cand.duration?.toFixed(1)}s
                                </span>
                              </div>

                              <button
                                onClick={() => handleCopy(cand)}
                                className="h-8 px-3 bg-[#f5f5f5] text-[#111111] rounded-full text-xs font-medium hover:bg-[#e5e5e5] active:scale-95 transition-all flex items-center gap-1 cursor-pointer border border-[#cacacb]/70"
                              >
                                {isCopied ? <Check className="w-3.5 h-3.5 text-[#007d48]" /> : <Copy className="w-3.5 h-3.5" />}
                                <span>{isCopied ? "Copied" : "Copy"}</span>
                              </button>
                            </div>

                            {/* Rating with Fire Emojis */}
                            {cand.composite_score !== undefined && (
                              <div className="flex items-center justify-between bg-[#f5f5f5]/70 p-2 border border-[#e5e5e5]">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-[#111111]">Rating:</span>
                                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border font-mono font-extrabold ${fire.badgeBg}`}>
                                    <span>{fire.emojis}</span>
                                    <span>{cand.composite_score.toFixed(1)} / 10</span>
                                  </span>
                                </div>
                                <span className={`font-bold uppercase text-[11px] ${fire.tagColor}`}>
                                  {fire.label}
                                </span>
                              </div>
                            )}

                            {/* Partitioning Divider */}
                            <div className="border-t border-[#e5e5e5] my-1" />

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div className="bg-[#f5f5f5] p-3 border-l-2 border-[#111111]">
                                <span className="text-[10px] uppercase font-bold text-[#707072] block mb-1">🪝 Hook Excerpt</span>
                                <p className="font-serif italic text-[#111111]">&ldquo;{cand.hook_text_safe}&rdquo;</p>
                              </div>
                              <div className="bg-[#f5f5f5] p-3 border-l-2 border-[#111111]">
                                <span className="text-[10px] uppercase font-bold text-[#707072] block mb-1">⚡ Cliffhanger Cut</span>
                                <p className="font-serif italic text-[#111111]">&ldquo;{cand.cliffhanger_text_safe}&rdquo;</p>
                              </div>
                            </div>

                            {/* Partitioning Divider */}
                            <div className="border-t border-[#e5e5e5] my-1" />

                            {cand.rationale && (
                              <div className="bg-[#f5f5f5] p-2.5 border border-[#e5e5e5] space-y-1">
                                <span className="text-[10px] font-bold uppercase text-[#707072] block">Why It Converts &middot; Rationale</span>
                                <p className="text-[#39393b] leading-relaxed">{cand.rationale}</p>
                              </div>
                            )}

                            {cand.repairs && cand.repairs.length > 0 && (
                              <p className="text-[11px] font-mono text-[#707072] bg-[#f5f5f5] p-2 border border-[#e5e5e5]">
                                <strong>Repairs:</strong> {cand.repairs.join("; ")}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
