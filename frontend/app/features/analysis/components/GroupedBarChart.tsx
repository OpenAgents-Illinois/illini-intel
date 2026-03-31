import { ChartItem } from "@/app/features/analysis/types";

interface GroupedBarChartProps {
  chart: ChartItem;
  opponentName?: string;
}

export function GroupedBarChart({ chart, opponentName = "Opponent" }: GroupedBarChartProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-4">{chart.title}</div>
      <div className="flex flex-col gap-4">
        {chart.series.map((item, i) => (
          <div key={i} className="space-y-1.5">
            <div className="text-xs text-zinc-400">{item.label}</div>
            <div className="flex items-center gap-2">
              <div className="w-16 text-[11px] text-orange-300 text-right shrink-0">{item.illinois}</div>
              <div className="flex-1 flex gap-1 h-3">
                <div className="flex-1 rounded-sm bg-orange-500/80" />
                <div className="flex-1 rounded-sm bg-blue-400/80" />
              </div>
              <div className="w-16 text-[11px] text-blue-300 shrink-0">{item.opponent}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-sm bg-orange-500" />
          <span className="text-xs text-zinc-500">Illinois</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-sm bg-blue-400" />
          <span className="text-xs text-zinc-500">{opponentName}</span>
        </div>
      </div>
    </div>
  );
}
