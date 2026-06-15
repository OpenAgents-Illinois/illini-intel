import { buildPredictionSummary } from "@/app/features/analysis/components/predictionText";
import { splitIntoParagraphs, highlightSegments } from "@/app/features/analysis/components/richText";

interface PredictionProps {
  content: string;
  winProbability: number | null;
  teamAName?: string;
}

export function Prediction({ content, winProbability, teamAName }: PredictionProps) {
  const paragraphs = splitIntoParagraphs(buildPredictionSummary(content, winProbability, teamAName));

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/30">
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
        Prediction
      </h3>
      <div className="space-y-3">
        {paragraphs.map((paragraph, index) => (
          <p key={index} className="text-sm leading-7 text-zinc-800 dark:text-zinc-200">
            {highlightSegments(paragraph).map((seg, i) =>
              seg.highlight ? (
                <span key={i} className="font-semibold text-emerald-700 dark:text-emerald-400">{seg.text}</span>
              ) : (
                <span key={i}>{seg.text}</span>
              )
            )}
          </p>
        ))}
      </div>
    </div>
  );
}
