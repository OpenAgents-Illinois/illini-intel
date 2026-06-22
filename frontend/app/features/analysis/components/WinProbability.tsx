import { getTeamColors } from "@/app/features/analysis/components/teamColors";

interface WinProbabilityProps {
  teamAProbability: number;
  teamAName?: string;
  teamBName?: string;
  teamAColor?: string;
  teamBColor?: string;
}

export const teamBProbability = (teamA: number) => 100 - teamA;

export function WinProbability({
  teamAProbability,
  teamAName = "Team A",
  teamBName = "Team B",
  teamAColor,
  teamBColor,
}: WinProbabilityProps) {
  const teamBProb = teamBProbability(teamAProbability);
  const teamAColors = getTeamColors(teamAColor, "a");
  const teamBColors = getTeamColors(teamBColor, "b");

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Win Probability</div>
      <div className="flex items-center justify-center gap-6">
        <div>
          <div className="text-xs text-zinc-500 mb-1">{teamAName}</div>
          <div className="text-4xl font-black" style={{ color: teamAColors.primary }}>
            {teamAProbability.toFixed(0)}%
          </div>
        </div>
        <div className="text-zinc-600">—</div>
        <div>
          <div className="text-xs text-zinc-500 mb-1">{teamBName}</div>
          <div className="text-4xl font-black" style={{ color: teamBColors.primary }}>
            {teamBProb.toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}
