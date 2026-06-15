import { applyEvent, initialStreamState } from "../state";

test("team_header event populates teamHeader with team_a/team_b", () => {
  const event = {
    type: "team_header" as const,
    team_a_rank: 3, team_a_name: "Illinois", team_a_mascot: "Fighting Illini",
    team_b_name: "UConn", team_b_mascot: "Huskies", team_b_rank: 1,
    game_context: "Final Four",
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.teamHeader?.team_a_name).toBe("Illinois");
  expect(next.teamHeader?.team_b_name).toBe("UConn");
});

test("stat_comparison appends with team_a/team_b values", () => {
  const event = {
    type: "stat_comparison" as const,
    label: "PPG", team_a_value: "87.3", team_b_value: "79.1", team_a_pct: 0.52,
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.statComparisons[0].team_a_value).toBe("87.3");
});

test("report_card carries team tag", () => {
  const event = {
    type: "report_card" as const,
    team: "team_b", dimension: "Defense", grade: "A-", stat: "x", explanation: "y",
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.reportCards[0].team).toBe("team_b");
});

test("win_probability sets winProbability from team_a_probability", () => {
  const next = applyEvent(initialStreamState, { type: "win_probability" as const, team_a_probability: 61 });
  expect(next.winProbability).toBe(61);
});
