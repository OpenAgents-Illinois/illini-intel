import { buildPredictionSummary } from "../components/predictionText";

test("buildPredictionSummary prepends structured probability", () => {
  expect(buildPredictionSummary("Illinois wins 78-74 with late free throws.", 61)).toBe(
    "Illinois has a 61% win probability. Illinois wins 78-74 with late free throws.",
  );
});

test("buildPredictionSummary falls back to content without probability", () => {
  expect(buildPredictionSummary("Illinois wins 78-74.", null)).toBe("Illinois wins 78-74.");
});
