import { TeamHeaderData } from "@/app/features/analysis/types";

interface TeamHeaderProps {
  data: TeamHeaderData;
  running: boolean;
}

export function TeamHeader({ data, running }: TeamHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-zinc-800 pb-4 mb-4">
      <div className="flex h-36 flex-col items-center justify-between text-center">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">AP Rank</div>
        <div className="text-4xl font-black text-orange-500">
          {data.illinois_rank != null ? `#${data.illinois_rank}` : "—"}
        </div>
        <div>
          <div className="text-sm font-bold text-white">{data.illinois_name.toUpperCase()}</div>
          <div className="text-xs text-zinc-600">{data.illinois_mascot}</div>
        </div>
      </div>

      <div className="text-center">
        <div className="text-xs text-zinc-600 uppercase tracking-widest">{data.game_context}</div>
        {running && (
          <div className="w-2 h-2 rounded-full bg-green-500 mx-auto mt-2 animate-pulse" />
        )}
      </div>

      <div className="flex h-36 flex-col items-center justify-between text-center">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">AP Rank</div>
        <div className="text-4xl font-black text-blue-400">
          {data.opponent_rank != null ? `#${data.opponent_rank}` : "—"}
        </div>
        <div>
          <div className="text-sm font-bold text-white">{data.opponent_name.toUpperCase()}</div>
          <div className="text-xs text-zinc-600">{data.opponent_mascot || "Opponent"}</div>
        </div>
      </div>
    </div>
  );
}
