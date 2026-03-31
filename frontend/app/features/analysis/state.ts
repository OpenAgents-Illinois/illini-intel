import { AgentEvent, StreamState } from "@/app/features/analysis/types";

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
  done: false,
};

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
      return {
        ...state,
        teamHeader: {
          illinois_rank: event.illinois_rank,
          illinois_name: event.illinois_name,
          illinois_mascot: event.illinois_mascot,
          opponent_name: event.opponent_name,
          opponent_mascot: event.opponent_mascot,
          opponent_rank: event.opponent_rank,
          game_context: event.game_context,
        },
      };
    case "stat_comparison":
      return { ...state, statComparisons: [...state.statComparisons, { label: event.label, illinois_value: event.illinois_value, opponent_value: event.opponent_value, illinois_pct: event.illinois_pct }] };
    case "report_card":
      return { ...state, reportCards: [...state.reportCards, { dimension: event.dimension, grade: event.grade, stat: event.stat, explanation: event.explanation }] };
    case "win_probability":
      return { ...state, winProbability: event.probability };
    case "done":
      return { ...state, running: false, done: true };
  }
}
