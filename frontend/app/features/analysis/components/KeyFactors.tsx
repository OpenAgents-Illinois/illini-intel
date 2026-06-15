import { KeyFactorItem } from "@/app/features/analysis/types";
import { getTeamColors } from "@/app/features/analysis/components/teamColors";

interface KeyFactorsProps {
  factors: KeyFactorItem[];
  teamAName?: string;
  teamBName?: string;
  teamAColor?: string;
  teamBColor?: string;
}

function cleanFactorLabel(label: string, teamAName: string, teamBName: string) {
  const escape = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return label
    .replace(new RegExp(`^${escape(teamAName)}\\s+`, "i"), "")
    .replace(new RegExp(`^${escape(teamBName)}\\s+`, "i"), "")
    .trim();
}

export function KeyFactors({ factors, teamAName = "Team A", teamBName = "Team B", teamAColor, teamBColor }: KeyFactorsProps) {
  if (factors.length === 0) return null;
  const teamAColors = getTeamColors(teamAColor, "a");
  const teamBColors = getTeamColors(teamBColor, "b");

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Key Factors</div>
      <div className="flex flex-col gap-3">
        {factors.map((factor, i) => {
          const favorsTeamA = factor.favors === "team_a";
          const color = favorsTeamA ? teamAColors.primary : teamBColors.secondary;
          const badge = favorsTeamA ? teamAName : teamBName;
          return (
            <div key={i} className="flex items-start gap-3">
              <div className="mt-1 w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-zinc-300">{cleanFactorLabel(factor.label, teamAName, teamBName)}</div>
                <div className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{factor.detail}</div>
              </div>
              <div className="text-[10px] font-bold uppercase shrink-0 mt-0.5" style={{ color }}>
                {badge}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
