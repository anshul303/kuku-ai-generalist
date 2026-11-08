export interface PromoCandidate {
  clip_id?: string;
  episode: number;
  start_time: number;
  end_time: number;
  start_formatted: string;
  end_formatted: string;
  duration: number;
  hook_beat_id?: string;
  cliffhanger_beat_id?: string;
  hook_text_safe: string;
  cliffhanger_text_safe: string;
  verdict: "PASS" | "REPAIR" | "FAIL" | string;
  composite_score?: number;
  hook_score?: number;
  cliffhanger_score?: number;
  standalone_score?: number;
  hook_passed?: boolean;
  cliffhanger_passed?: boolean;
  standalone_passed?: boolean;
  rationale?: string;
  judge_rationale?: string;
  spoiler_note?: string;
  repairs?: string[];
  rank?: number;
  episode_logline?: string;
}

export interface EpisodeData {
  episode: number;
  logline: string;
  total_beats: number;
  candidates: PromoCandidate[];
}

export interface RunMetadata {
  timestamp?: string;
  model_requested?: string;
  api_model_version_returned?: string;
  observed_model_behavior?: string;
  runtime_seconds?: number;
  total_calls?: number;
  cache_hits?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  estimated_paid_tier_equivalent_usd?: number;
  actual_free_tier_cost_usd?: number;
  repair_reject_stats?: {
    total_proposed: number;
    total_validated: number;
    total_repaired: number;
    repair_rate: number;
    total_rejected: number;
    reject_rate: number;
  };
  judge_score_distribution?: {
    total_judged: number;
    survivors: number;
    scores_equal_8_0: number;
    fraction_score_8_0: number;
    mean_composite_score: number;
  };
}

export interface DatasetPayload {
  meta: RunMetadata;
  top15: PromoCandidate[];
  episodes: EpisodeData[];
  total_candidates: number;
  total_survivors: number;
}
