import { normalizeComparisons } from "../components/statComparison";

test("normalizeComparisons filters placeholder labels", () => {
  expect(
    normalizeComparisons([
      { label: "Stat", illinois_value: "87.1", opponent_value: "81.2", illinois_pct: 1 },
      { label: "Tempo", illinois_value: "73.1", opponent_value: "69.4", illinois_pct: 0.57 },
    ]),
  ).toEqual([
    { label: "Tempo", illinois_value: "73.1", opponent_value: "69.4", illinois_pct: 0.57 },
  ]);
});

test("normalizeComparisons drops uniformly extreme junk rows", () => {
  expect(
    normalizeComparisons([
      { label: "Tempo", illinois_value: "73.1", opponent_value: "69.4", illinois_pct: 1 },
      { label: "Rebounding", illinois_value: "39.0", opponent_value: "31.2", illinois_pct: 1 },
      { label: "Turnovers", illinois_value: "10.2", opponent_value: "13.4", illinois_pct: 1 },
    ]),
  ).toEqual([]);
});
