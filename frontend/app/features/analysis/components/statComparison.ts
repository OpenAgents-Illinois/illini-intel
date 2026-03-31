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
    if (!Number.isFinite(item.illinois_pct) || item.illinois_pct < 0 || item.illinois_pct > 1) {
      return false;
    }
    if (isPlaceholderText(item.illinois_value) && isPlaceholderText(item.opponent_value)) {
      return false;
    }
    if (seen.has(dedupeKey)) return false;

    seen.add(dedupeKey);
    return true;
  });

  return normalized.slice(0, 4);
}
