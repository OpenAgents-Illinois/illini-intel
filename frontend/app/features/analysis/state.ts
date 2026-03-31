import { AgentEvent, StreamState, TeamHeaderData } from "@/app/features/analysis/types";

export const initialStreamState: StreamState = {
  running: false,
  thoughts: [],
  toolCalls: [],
  insightCards: [],
  matchupPreview: null,
  prediction: null,
  teamHeader: null,
  statComparisons: [],
  reportCards: [],
  winProbability: null,
  recentForms: [],
  keyFactors: [],
  charts: [],
  done: false,
};

function normalizeTeamHeader(event: Extract<AgentEvent, { type: "team_header" }>): TeamHeaderData {
  const legacyOpponentName = (event as { opponent_name?: string }).opponent_name;
  return {
    illinois_rank: event.illinois_rank,
    illinois_name:
      (event as { illinois_name?: string }).illinois_name ?? "Illinois",
    illinois_mascot:
      (event as { illinois_mascot?: string }).illinois_mascot ?? "Fighting Illini",
    opponent_name: legacyOpponentName ?? "Opponent",
    opponent_mascot:
      (event as { opponent_mascot?: string }).opponent_mascot ?? "",
    opponent_rank: event.opponent_rank,
    game_context: event.game_context ?? "Illinois Basketball",
  };
}

export function applyEvent(state: StreamState, event: AgentEvent): StreamState {
  switch (event.type) {
    case "agent_thought":
      return { ...state, thoughts: [...state.thoughts, { agent: event.agent, content: event.content }] };
    case "tool_call":
      return { ...state, toolCalls: [...state.toolCalls, { agent: event.agent, tool: event.tool, args: event.args }] };
    case "tool_result":
      return state;
    case "insight_card":
      return { ...state, insightCards: [...state.insightCards, { title: event.title, data: event.data }] };
    case "matchup_preview":
      return { ...state, matchupPreview: event.content };
    case "prediction":
      return { ...state, prediction: event.content };
    case "team_header":
      return { ...state, teamHeader: normalizeTeamHeader(event) };
    case "stat_comparison":
      return { ...state, statComparisons: [...state.statComparisons, { label: event.label, illinois_value: event.illinois_value, opponent_value: event.opponent_value, illinois_pct: event.illinois_pct }] };
    case "report_card":
      return { ...state, reportCards: [...state.reportCards, { dimension: event.dimension, grade: event.grade, stat: event.stat, explanation: event.explanation }] };
    case "win_probability":
      return { ...state, winProbability: event.probability };
    case "recent_form":
      return { ...state, recentForms: [...state.recentForms, { team: event.team, results: event.results }] };
    case "key_factor":
      return { ...state, keyFactors: [...state.keyFactors, { label: event.label, detail: event.detail, favors: event.favors }] };
    case "chart":
      return { ...state, charts: [...state.charts, { chart_type: event.chart_type, title: event.title, series: event.series }] };
    case "done":
      return { ...state, running: false, done: true };
  }
}
