import { getIllinoisColors, getOpponentColors } from "@/app/features/analysis/components/teamColors";

interface WinProbabilityProps {
  probability: number;
  opponentName?: string;
  opponentColor?: string;
}

export function WinProbability({ probability, opponentName, opponentColor }: WinProbabilityProps) {
  const illinoisLeads = probability >= 50;
  const illinoisColors = getIllinoisColors();
  const opponentColors = getOpponentColors(opponentName, opponentColor);
  const color = illinoisLeads ? illinoisColors.primary : opponentColors.secondary;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">Illinois Win Probability</div>
      <div className="text-5xl font-black" style={{ color }}>
        {probability.toFixed(0)}%
      </div>
    </div>
  );
}
