export interface ChartSeriesItem {
  label: string;
  illinois: string;
  opponent: string;
}

export interface ChartItem {
  chart_type: string;
  title: string;
  series: ChartSeriesItem[];
}

export type AgentEvent =
  | { type: "agent_thought"; agent: string; content: string }
  | { type: "tool_call"; agent: string; tool: string; args: unknown }
  | { type: "tool_result"; agent: string; tool: string; result: unknown }
  | { type: "insight_card"; title: string; data: Record<string, unknown> }
  | { type: "matchup_preview"; content: string }
  | { type: "prediction"; content: string }
  | { type: "team_header"; illinois_rank: number | null; illinois_name: string; illinois_mascot: string; illinois_color?: string; opponent_name: string; opponent_mascot: string; opponent_rank: number | null; opponent_color?: string; game_context: string }
  | { type: "stat_comparison"; label: string; illinois_value: string; opponent_value: string; illinois_pct: number }
  | { type: "report_card"; dimension: string; grade: string; stat: string; explanation: string }
  | { type: "win_probability"; probability: number }
  | { type: "recent_form"; team: string; results: string[] }
  | { type: "key_factor"; label: string; detail: string; favors: string }
  | { type: "chart"; chart_type: string; title: string; series: ChartSeriesItem[] }
  | { type: "done" };

export interface ThoughtItem {
  agent: string;
  content: string;
}

export interface ToolCallItem {
  agent: string;
  tool: string;
  args: unknown;
}

export interface InsightCardItem {
  title: string;
  data: Record<string, unknown>;
}

export interface TeamHeaderData {
  illinois_rank: number | null;
  illinois_name: string;
  illinois_mascot: string;
  illinois_color?: string;
  opponent_name: string;
  opponent_mascot: string;
  opponent_rank: number | null;
  opponent_color?: string;
  game_context: string;
}

export interface StatComparisonItem {
  label: string;
  illinois_value: string;
  opponent_value: string;
  illinois_pct: number;
}

export interface ReportCardItem {
  dimension: string;
  grade: string;
  stat: string;
  explanation: string;
}

export interface RecentFormItem {
  team: string;
  results: string[];
}

export interface KeyFactorItem {
  label: string;
  detail: string;
  favors: string;
}

export interface StreamState {
  running: boolean;
  thoughts: ThoughtItem[];
  toolCalls: ToolCallItem[];
  insightCards: InsightCardItem[];
  matchupPreview: string | null;
  prediction: string | null;
  teamHeader: TeamHeaderData | null;
  statComparisons: StatComparisonItem[];
  reportCards: ReportCardItem[];
  winProbability: number | null;
  recentForms: RecentFormItem[];
  keyFactors: KeyFactorItem[];
  charts: ChartItem[];
  done: boolean;
}
