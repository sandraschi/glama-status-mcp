export interface Tool {
  name: string;
  grade?: string;
  score: number;
  purpose: number;
  usage_guidelines: number;
  behavior: number;
  parameters: number;
  conciseness: number;
  completeness: number;
}

export interface Repo {
  name: string;
  overall_grade?: string;
  overall_score?: number;
  tdqs_grade?: string;
  tdqs_mean?: number;
  tdqs_min?: number;
  coherence_grade?: string;
  coherence_disambiguation?: number;
  coherence_naming?: number;
  coherence_tool_count?: number;
  coherence_completeness?: number;
  maintenance_grade?: string;
  profile_completion?: number;
  latest_release?: string;
  last_scraped?: string;
  tools?: Tool[];
  days_stale?: number;
}
