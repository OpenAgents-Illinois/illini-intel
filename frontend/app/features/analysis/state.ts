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
  done: false,
};

function normalizeTeamHeader(event: Extract<AgentEvent, { type: "team_header" }>): TeamHeaderData {
  return {
    team_a_rank: event.team_a_rank,
    team_a_name: event.team_a_name ?? "Team A",
    team_a_mascot: event.team_a_mascot ?? "",
    team_a_color: event.team_a_color,
    team_b_name: event.team_b_name ?? "Team B",
    team_b_mascot: event.team_b_mascot ?? "",
    team_b_rank: event.team_b_rank,
    team_b_color: event.team_b_color,
    game_context: event.game_context ?? "Matchup",
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
      return { ...state, statComparisons: [...state.statComparisons, { label: event.label, team_a_value: event.team_a_value, team_b_value: event.team_b_value, team_a_pct: event.team_a_pct }] };
    case "report_card":
      return { ...state, reportCards: [...state.reportCards, { team: event.team, dimension: event.dimension, grade: event.grade, stat: event.stat, explanation: event.explanation }] };
    case "win_probability":
      return { ...state, winProbability: event.team_a_probability };
    case "recent_form":
      return { ...state, recentForms: [...state.recentForms, { team: event.team, results: event.results }] };
    case "key_factor":
      return { ...state, keyFactors: [...state.keyFactors, { label: event.label, detail: event.detail, favors: event.favors }] };
    case "done":
      return { ...state, running: false, done: true };
  }
}
