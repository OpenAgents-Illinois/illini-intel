import { StatComparisonItem } from "@/app/features/analysis/types";

interface StatComparisonChartProps {
  comparisons: StatComparisonItem[];
}

export function StatComparisonChart({ comparisons }: StatComparisonChartProps) {
  if (comparisons.length === 0) return null;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Category Breakdown</div>
      <div className="flex flex-col gap-3">
        {comparisons.map((item) => {
          const illinoisLeads = item.illinois_pct >= 0.5;
          const pct = Math.round(item.illinois_pct * 100);
          return (
            <div key={item.label} className="flex items-center gap-3">
              <div className="w-24 text-xs text-zinc-400 text-right">{item.label}</div>
              <div className="flex-1 bg-zinc-800 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full ${illinoisLeads ? "bg-orange-500" : "bg-blue-400"}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <div className={`w-8 text-xs font-bold ${illinoisLeads ? "text-orange-400" : "text-blue-400"}`}>
                {pct}%
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-sm bg-orange-500" />
          <span className="text-xs text-zinc-500">Illinois edge</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-sm bg-blue-400" />
          <span className="text-xs text-zinc-500">Opponent edge</span>
        </div>
      </div>
    </div>
  );
}
