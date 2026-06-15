import { teamBProbability } from "../components/WinProbability";

test("derives team_b probability as 100 - team_a", () => {
  expect(teamBProbability(61)).toBeCloseTo(39);
  expect(teamBProbability(0)).toBeCloseTo(100);
});
