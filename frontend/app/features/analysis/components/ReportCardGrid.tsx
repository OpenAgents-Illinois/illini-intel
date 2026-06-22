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
  teamAName?: string;
  teamBName?: string;
}

function GradeCard({ card }: { card: ReportCardItem }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-3">
      <div className="text-xs text-zinc-500 uppercase mb-1">{card.dimension}</div>
      <div className={`text-3xl font-black ${GRADE_COLORS[card.grade] ?? "text-zinc-400"}`}>{card.grade}</div>
      <div className="text-xs text-zinc-300 font-medium mt-1">{card.stat}</div>
      <div className="text-xs text-zinc-500 mt-0.5">{card.explanation}</div>
    </div>
  );
}

export function ReportCardGrid({ cards, teamAName = "Team A", teamBName = "Team B" }: ReportCardGridProps) {
  if (cards.length === 0) return null;

  const columns: Array<{ name: string; group: ReportCardItem[] }> = [
    { name: teamAName, group: cards.filter((c) => c.team === "team_a") },
    { name: teamBName, group: cards.filter((c) => c.team === "team_b") },
  ];

  return (
    <div>
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Dimension Report Cards</div>
      <div className="grid grid-cols-2 gap-4">
        {columns.map((column) => (
          <div key={column.name}>
            <div className="text-xs font-semibold text-zinc-400 mb-2">{column.name}</div>
            <div className="grid grid-cols-1 gap-3">
              {column.group.map((card) => (
                <GradeCard key={`${card.team}-${card.dimension}`} card={card} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
