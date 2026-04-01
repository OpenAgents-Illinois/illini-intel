import { KeyFactorItem } from "@/app/features/analysis/types";
import { getIllinoisColors, getOpponentColors } from "@/app/features/analysis/components/teamColors";

interface KeyFactorsProps {
  factors: KeyFactorItem[];
  opponentName?: string;
  opponentColor?: string;
}

function cleanFactorLabel(label: string, opponentName: string) {
  const escapedOpponent = opponentName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return label
    .replace(/^Illinois\s+/i, "")
    .replace(new RegExp(`^${escapedOpponent}\\s+`, "i"), "")
    .trim();
}

export function KeyFactors({ factors, opponentName = "Opponent", opponentColor }: KeyFactorsProps) {
  if (factors.length === 0) return null;
  const illinoisColors = getIllinoisColors();
  const opponentColors = getOpponentColors(opponentName, opponentColor);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Key Factors</div>
      <div className="flex flex-col gap-3">
        {factors.map((factor, i) => (
          <div key={i} className="flex items-start gap-3">
            <div
              className="mt-1 w-2 h-2 rounded-full shrink-0"
              style={{
                backgroundColor:
                  factor.favors === "illinois"
                    ? illinoisColors.primary
                    : factor.favors === "opponent"
                    ? opponentColors.secondary
                    : "#71717a",
              }}
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-zinc-300">{cleanFactorLabel(factor.label, opponentName)}</div>
              <div className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{factor.detail}</div>
            </div>
            <div
              className="text-[10px] font-bold uppercase shrink-0 mt-0.5"
              style={{
                color:
                  factor.favors === "illinois"
                    ? illinoisColors.primary
                    : factor.favors === "opponent"
                    ? opponentColors.secondary
                    : "#71717a",
              }}
            >
              {factor.favors === "illinois" ? "ILL" : factor.favors === "opponent" ? opponentName : "EVEN"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
