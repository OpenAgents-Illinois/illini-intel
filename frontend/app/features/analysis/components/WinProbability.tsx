interface WinProbabilityProps {
  probability: number;
}

export function WinProbability({ probability }: WinProbabilityProps) {
  const illinoisLeads = probability >= 50;
  return (
    <div className={`rounded-xl border p-4 text-center ${illinoisLeads ? "border-green-800 bg-green-950/30" : "border-zinc-700 bg-zinc-900"}`}>
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-1">Illinois Win Probability</div>
      <div className={`text-5xl font-black ${illinoisLeads ? "text-green-400" : "text-zinc-400"}`}>
        {probability.toFixed(0)}%
      </div>
    </div>
  );
}
