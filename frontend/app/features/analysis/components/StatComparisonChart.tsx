import { StatComparisonItem } from "@/app/features/analysis/types";
import { normalizeComparisons } from "@/app/features/analysis/components/statComparison";
import { getIllinoisColors, getOpponentColors } from "@/app/features/analysis/components/teamColors";

interface StatComparisonChartProps {
  comparisons: StatComparisonItem[];
  opponentName?: string;
  opponentColor?: string;
}

export function StatComparisonChart({ comparisons, opponentName = "Opponent", opponentColor }: StatComparisonChartProps) {
  const normalizedComparisons = normalizeComparisons(comparisons);
  const illinoisColors = getIllinoisColors();
  const opponentColors = getOpponentColors(opponentName, opponentColor);

  if (normalizedComparisons.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-2">Category Breakdown</div>
        <p className="text-sm text-zinc-600">Stat comparison unavailable — insufficient opponent data.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Category Breakdown</div>
      <div className="flex flex-col gap-3">
        {normalizedComparisons.map((item, index) => {
          const illinoisLeads = item.illinois_pct >= 0.5;
          const pct = Math.round(item.illinois_pct * 100);
          const opponentPct = 100 - pct;
          return (
            <div key={`${item.label}-${index}`} className="grid grid-cols-[96px_minmax(0,1fr)_56px] items-center gap-3">
              <div className="text-xs text-zinc-400 text-right">{item.label}</div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px] text-zinc-500">
                  <span style={{ color: illinoisLeads ? illinoisColors.accentText : undefined }}>{item.illinois_value}</span>
                  <span style={{ color: !illinoisLeads ? opponentColors.accentText : undefined }}>{item.opponent_value}</span>
                </div>
                <div className="flex h-3 overflow-hidden rounded-full bg-zinc-800">
                  <div className="h-full" style={{ width: `${pct}%`, backgroundColor: illinoisColors.primary }} />
                  <div className="h-full" style={{ width: `${opponentPct}%`, backgroundColor: opponentColors.secondary }} />
                </div>
              </div>
              <div className="text-xs font-bold" style={{ color: illinoisLeads ? illinoisColors.primary : opponentColors.secondary }}>
                {pct}%
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: illinoisColors.primary }} />
          <span className="text-xs text-zinc-500">Illinois edge</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: opponentColors.secondary }} />
          <span className="text-xs text-zinc-500">{opponentName} edge</span>
        </div>
      </div>
    </div>
  );
}
