import { StatComparisonItem } from "@/app/features/analysis/types";

function isPlaceholderText(value: string) {
  const normalized = value.trim().toLowerCase();
  return normalized === "" || normalized === "-" || normalized === "none" || normalized === "stat" || normalized === "metric";
}

export function normalizeComparisons(comparisons: StatComparisonItem[]) {
  const seen = new Set<string>();
  const normalized = comparisons.filter((item) => {
    const label = item.label.trim();
    const dedupeKey = label.toLowerCase();

    if (isPlaceholderText(label)) return false;
    if (!Number.isFinite(item.team_a_pct) || item.team_a_pct < 0 || item.team_a_pct > 1) {
      return false;
    }
    if (isPlaceholderText(item.team_a_value) || isPlaceholderText(item.team_b_value)) {
      return false;
    }
    if (seen.has(dedupeKey)) return false;

    seen.add(dedupeKey);
    return true;
  });

  const sliced = normalized.slice(0, 4);

  // Drop degenerate sets where every row is pinned to the same extreme (0 or 1) —
  // a sign the model emitted junk confidence rather than real percentages.
  const allSameExtreme =
    sliced.length >= 2 &&
    sliced.every((item) => item.team_a_pct === sliced[0].team_a_pct) &&
    (sliced[0].team_a_pct === 0 || sliced[0].team_a_pct === 1);

  return allSameExtreme ? [] : sliced;
}
