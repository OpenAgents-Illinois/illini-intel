import { TeamHeaderData, RecentFormItem } from "@/app/features/analysis/types";
import { getTeamColors } from "@/app/features/analysis/components/teamColors";

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
  const teamAName = data.team_a_name || "Team A";
  const teamAMascot = data.team_a_mascot || "";
  const teamBName = data.team_b_name || "Team B";
  const teamBMascot = data.team_b_mascot || "";
  const teamAColors = getTeamColors(data.team_a_color, "a");
  const teamBColors = getTeamColors(data.team_b_color, "b");

  const teamAForm = recentForms.find((f) => f.team === teamAName)?.results ?? recentForms[0]?.results ?? [];
  const teamBForm = recentForms.find((f) => f.team === teamBName)?.results ?? recentForms[1]?.results ?? [];

  return (
    <div className="flex items-center justify-between border-b border-zinc-800 pb-4 mb-4">
      <div className="flex flex-col items-center text-center">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">AP Rank</div>
        <div className="text-4xl font-black" style={{ color: teamAColors.primary }}>
          {data.team_a_rank != null ? `#${data.team_a_rank}` : "—"}
        </div>
        <div className="mt-2">
          <div className="text-sm font-bold text-white">{teamAName.toUpperCase()}</div>
          <div className="text-xs text-zinc-600">{teamAMascot}</div>
        </div>
        <FormBubbles results={teamAForm} />
      </div>

      <div className="text-center">
        <div className="text-xs text-emerald-500 uppercase tracking-widest font-semibold">{data.game_context}</div>
        {running && (
          <div className="w-2 h-2 rounded-full bg-green-500 mx-auto mt-2 animate-pulse" />
        )}
      </div>

      <div className="flex flex-col items-center text-center">
        <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">AP Rank</div>
        <div className="text-4xl font-black" style={{ color: teamBColors.primary }}>
          {data.team_b_rank != null ? `#${data.team_b_rank}` : "—"}
        </div>
        <div className="mt-2">
          <div className="text-sm font-bold text-white">{teamBName.toUpperCase()}</div>
          <div className="text-xs text-zinc-600">{teamBMascot}</div>
        </div>
        <FormBubbles results={teamBForm} />
      </div>
    </div>
  );
}
