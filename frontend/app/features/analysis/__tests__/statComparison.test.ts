import { normalizeComparisons } from "../components/statComparison";

test("normalizeComparisons filters placeholder labels", () => {
  expect(
    normalizeComparisons([
      { label: "Stat", team_a_value: "87.1", team_b_value: "81.2", team_a_pct: 1 },
      { label: "Tempo", team_a_value: "73.1", team_b_value: "69.4", team_a_pct: 0.57 },
    ]),
  ).toEqual([
    { label: "Tempo", team_a_value: "73.1", team_b_value: "69.4", team_a_pct: 0.57 },
  ]);
});

test("normalizeComparisons drops uniformly extreme junk rows", () => {
  expect(
    normalizeComparisons([
      { label: "Tempo", team_a_value: "73.1", team_b_value: "69.4", team_a_pct: 1 },
      { label: "Rebounding", team_a_value: "39.0", team_b_value: "31.2", team_a_pct: 1 },
      { label: "Turnovers", team_a_value: "10.2", team_b_value: "13.4", team_a_pct: 1 },
    ]),
  ).toEqual([]);
});
