import { PromoCandidate, EpisodeData } from "../types";

/**
 * Extracts a target episode number from search query:
 * Handles: "3", "03", "ep 3", "ep03", "ep 03", "e3", "e03", "episode 3", "episode 03", "ep. 3", "ep.03"
 */
export function extractTargetEpisodeNumber(query: string): number | null {
  if (!query) return null;
  const q = query.trim().toLowerCase();

  // Pattern: "ep 3", "ep03", "e3", "e03", "episode 3", "ep. 3", "ep.03", "ep-03"
  const epPattern = /^(?:ep(?:isode)?\.?|e)[\s\-_#]*0*([1-9][0-9]?)$/i;
  const match = q.match(epPattern);
  if (match) {
    return parseInt(match[1], 10);
  }

  // Pure integer: "3" or "03" or "45"
  const pureNum = parseInt(q, 10);
  if (!isNaN(pureNum) && String(pureNum) === q.replace(/^0+/, "") && pureNum >= 1 && pureNum <= 50) {
    return pureNum;
  }

  return null;
}

/**
 * Extracts target rank: "#1", "rank 1", "rank #1", "top 1"
 */
export function extractTargetRank(query: string): number | null {
  if (!query) return null;
  const q = query.trim().toLowerCase();
  const rankPattern = /^(?:rank|top)?\s*#?\s*([1-9]|1[0-5])$/i;
  const match = q.match(rankPattern);
  if (match) {
    return parseInt(match[1], 10);
  }
  return null;
}

/**
 * Matches a PromoCandidate against the user's search query
 */
export function matchesPromo(promo: PromoCandidate, query: string): boolean {
  if (!query || !query.trim()) return true;
  const q = query.trim().toLowerCase();

  // 1. Direct episode number match
  const targetEp = extractTargetEpisodeNumber(q);
  if (targetEp !== null) {
    return promo.episode === targetEp;
  }

  // 2. Direct rank match
  const targetRank = extractTargetRank(q);
  if (targetRank !== null) {
    return promo.rank === targetRank;
  }

  // 3. Normalized multi-token text search
  const tokens = q.split(/\s+/).filter(Boolean);
  const corpus = [
    `episode ${promo.episode}`,
    `ep ${promo.episode}`,
    `ep${promo.episode}`,
    `e${promo.episode < 10 ? `0${promo.episode}` : promo.episode}`,
    `e${promo.episode}`,
    promo.clip_id || "",
    promo.start_formatted || "",
    promo.end_formatted || "",
    promo.hook_beat_id || "",
    promo.cliffhanger_beat_id || "",
    promo.hook_text_safe || "",
    (promo as any).hook_text || "",
    promo.cliffhanger_text_safe || "",
    (promo as any).cliffhanger_text || "",
    promo.rationale || "",
    promo.judge_rationale || "",
    (promo as any).rank_rationale || "",
    promo.episode_logline || "",
    promo.spoiler_note || "",
    promo.verdict || "",
  ].join(" ").toLowerCase();

  return tokens.every((token) => corpus.includes(token));
}

/**
 * Matches an EpisodeData against the user's search query
 */
export function matchesEpisode(ep: EpisodeData, query: string): boolean {
  if (!query || !query.trim()) return true;
  const q = query.trim().toLowerCase();

  // 1. Direct episode number match
  const targetEp = extractTargetEpisodeNumber(q);
  if (targetEp !== null) {
    return ep.episode === targetEp;
  }

  // 2. Multi-token text search over episode metadata and all candidates
  const tokens = q.split(/\s+/).filter(Boolean);
  const candidateTexts: string[] = [];
  if (ep.candidates) {
    for (const c of ep.candidates) {
      candidateTexts.push(
        c.start_formatted || "",
        c.end_formatted || "",
        c.clip_id || "",
        c.hook_beat_id || "",
        c.cliffhanger_beat_id || "",
        c.hook_text_safe || "",
        (c as any).hook_text || "",
        c.cliffhanger_text_safe || "",
        (c as any).cliffhanger_text || "",
        c.rationale || "",
        c.judge_rationale || "",
        c.verdict || ""
      );
    }
  }

  const corpus = [
    `episode ${ep.episode}`,
    `ep ${ep.episode}`,
    `ep${ep.episode}`,
    `e${ep.episode < 10 ? `0${ep.episode}` : ep.episode}`,
    `e${ep.episode}`,
    ep.logline || "",
    ...candidateTexts,
  ].join(" ").toLowerCase();

  return tokens.every((token) => corpus.includes(token));
}
