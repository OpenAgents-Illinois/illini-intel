import { TeamHeaderData, RecentFormItem } from "@/app/features/analysis/types";
import { getIllinoisColors, getOpponentColors } from "@/app/features/analysis/components/teamColors";

interface TeamHeaderProps {
  data: TeamHeaderData;
  running: boolean;
  recentForms?: RecentFormItem[];
}

function FormBubbles({ results }: { results: string[] }) {
  if (results.length === 0) return null;
  return (
    <div className="flex gap-1 mt-1.5 justify-center">
      {results.map((r, i) => (
        <div
          key={i}
          className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-white ${
            r === "W" ? "bg-emerald-600" : "bg-red-600"
          }`}
        >
          {r}
        </div>
      ))}
    </div>
  );
}

export function TeamHeader({ data, running, recentForms = [] }: TeamHeaderProps) {
  const illinoisName = data.illinois_name || "Illinois";
  const illinoisMascot = data.illinois_mascot || "Fighting Illini";
  const opponentName = data.opponent_name || "Opponent";
  const opponentMascot = data.opponent_mascot || "";
  const illinoisColors = getIllinoisColors();
  const opponentColors = getOpponentColors(opponentName, data.opponent_color);

  const illinoisForm = recentForms.find(f => f.team.toLowerCase().includes("illinois"))?.results ?? [];
  const opponentForm = recentForms.find(f => !f.team.toLowerCase().includes("illinois"))?.results ?? [];

  return (
    <div className="flex items-center justify-between border-b border-zinc-800 pb-4 mb-4">
      <div className="flex flex-col items-center text-center">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">AP Rank</div>
        <div className="text-4xl font-black" style={{ color: illinoisColors.primary }}>
          {data.illinois_rank != null ? `#${data.illinois_rank}` : "—"}
        </div>
        <div className="mt-2">
          <div className="text-sm font-bold text-white">{illinoisName.toUpperCase()}</div>
          <div className="text-xs text-zinc-600">{illinoisMascot}</div>
        </div>
        <FormBubbles results={illinoisForm} />
      </div>

      <div className="text-center">
        <div className="text-xs text-emerald-500 uppercase tracking-widest font-semibold">{data.game_context}</div>
        {running && (
          <div className="w-2 h-2 rounded-full bg-green-500 mx-auto mt-2 animate-pulse" />
        )}
      </div>

      <div className="flex flex-col items-center text-center">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">AP Rank</div>
        <div className="text-4xl font-black" style={{ color: opponentColors.secondary }}>
          {data.opponent_rank != null ? `#${data.opponent_rank}` : "—"}
        </div>
        <div className="mt-2">
          <div className="text-sm font-bold text-white">{opponentName.toUpperCase()}</div>
          <div className="text-xs text-zinc-600">{opponentMascot || "Opponent"}</div>
        </div>
        <FormBubbles results={opponentForm} />
      </div>
    </div>
  );
}
