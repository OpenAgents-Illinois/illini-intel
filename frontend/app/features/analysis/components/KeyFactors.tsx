import { KeyFactorItem } from "@/app/features/analysis/types";

interface KeyFactorsProps {
  factors: KeyFactorItem[];
}

export function KeyFactors({ factors }: KeyFactorsProps) {
  if (factors.length === 0) return null;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Key Factors</div>
      <div className="flex flex-col gap-3">
        {factors.map((factor, i) => (
          <div key={i} className="flex items-start gap-3">
            <div
              className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                factor.favors === "illinois"
                  ? "bg-orange-500"
                  : factor.favors === "opponent"
                  ? "bg-blue-400"
                  : "bg-zinc-500"
              }`}
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-zinc-300">{factor.label}</div>
              <div className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{factor.detail}</div>
            </div>
            <div
              className={`text-[10px] font-bold uppercase shrink-0 mt-0.5 ${
                factor.favors === "illinois"
                  ? "text-orange-400"
                  : factor.favors === "opponent"
                  ? "text-blue-400"
                  : "text-zinc-500"
              }`}
            >
              {factor.favors === "illinois" ? "ILL" : factor.favors === "opponent" ? "OPP" : "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
