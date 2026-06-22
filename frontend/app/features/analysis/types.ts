export type AgentEvent =
  | { type: "agent_thought"; agent: string; content: string }
  | { type: "tool_call"; agent: string; tool: string; args: unknown }
  | { type: "tool_result"; agent: string; tool: string; result: unknown }
  | { type: "insight_card"; title: string; data: Record<string, unknown> }
  | { type: "matchup_preview"; content: string }
  | { type: "prediction"; content: string }
  | { type: "team_header"; team_a_rank: number | null; team_a_name: string; team_a_mascot: string; team_a_color?: string; team_b_name: string; team_b_mascot: string; team_b_rank: number | null; team_b_color?: string; game_context: string }
  | { type: "stat_comparison"; label: string; team_a_value: string; team_b_value: string; team_a_pct: number }
  | { type: "report_card"; team: string; dimension: string; grade: string; stat: string; explanation: string }
  | { type: "win_probability"; team_a_probability: number }
  | { type: "recent_form"; team: string; results: string[] }
  | { type: "key_factor"; label: string; detail: string; favors: string }
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
  team_a_rank: number | null;
  team_a_name: string;
  team_a_mascot: string;
  team_a_color?: string;
  team_b_name: string;
  team_b_mascot: string;
  team_b_rank: number | null;
  team_b_color?: string;
  game_context: string;
}

export interface StatComparisonItem {
  label: string;
  team_a_value: string;
  team_b_value: string;
  team_a_pct: number;
}

export interface ReportCardItem {
  team: string;
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
  done: boolean;
}
