import { ReportCardItem } from "@/app/features/analysis/types";

const GRADE_COLORS: Record<string, string> = {
  "A+": "text-green-400",
  "A": "text-green-400",
  "A-": "text-green-400",
  "B+": "text-yellow-400",
  "B": "text-yellow-400",
  "B-": "text-yellow-400",
  "C+": "text-orange-400",
  "C": "text-orange-400",
};

interface ReportCardGridProps {
  cards: ReportCardItem[];
}

export function ReportCardGrid({ cards }: ReportCardGridProps) {
  if (cards.length === 0) return null;

  return (
    <div>
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Dimension Report Cards</div>
      <div className="grid grid-cols-2 gap-3">
        {cards.map((card) => (
          <div key={card.dimension} className="rounded-xl border border-zinc-800 bg-zinc-900 p-3">
            <div className="text-xs text-zinc-500 uppercase mb-1">{card.dimension}</div>
            <div className={`text-3xl font-black ${GRADE_COLORS[card.grade] ?? "text-zinc-400"}`}>
              {card.grade}
            </div>
            <div className="text-xs text-zinc-300 font-medium mt-1">{card.stat}</div>
            <div className="text-xs text-zinc-500 mt-0.5">{card.explanation}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
