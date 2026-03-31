import { applyEvent, initialStreamState } from "../state";

test("team_header event populates teamHeader", () => {
  const event = {
    type: "team_header" as const,
    illinois_rank: 3,
    opponent_name: "UConn",
    opponent_rank: 1,
    game_context: "Final Four",
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.teamHeader).toEqual({
    illinois_rank: 3,
    opponent_name: "UConn",
    opponent_rank: 1,
    game_context: "Final Four",
  });
});

test("stat_comparison event appends to statComparisons", () => {
  const event = {
    type: "stat_comparison" as const,
    label: "PPG",
    illinois_value: "87.3",
    opponent_value: "79.1",
    illinois_pct: 0.52,
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.statComparisons).toHaveLength(1);
  expect(next.statComparisons[0].label).toBe("PPG");
});

test("report_card event appends to reportCards", () => {
  const event = {
    type: "report_card" as const,
    dimension: "Offense",
    grade: "A+",
    stat: "87.3 PPG",
    explanation: "Top 5 nationally",
  };
  const next = applyEvent(initialStreamState, event);
  expect(next.reportCards).toHaveLength(1);
  expect(next.reportCards[0].grade).toBe("A+");
});

test("win_probability event sets winProbability", () => {
  const event = { type: "win_probability" as const, probability: 61.0 };
  const next = applyEvent(initialStreamState, event);
  expect(next.winProbability).toBe(61.0);
});
