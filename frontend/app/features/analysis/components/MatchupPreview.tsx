import { splitIntoParagraphs, highlightSegments } from "@/app/features/analysis/components/richText";

interface MatchupPreviewProps {
  content: string;
}

export function MatchupPreview({ content }: MatchupPreviewProps) {
  const paragraphs = splitIntoParagraphs(content);

  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950/30">
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-400">
        Matchup Preview
      </h3>
      <div className="space-y-3">
        {paragraphs.map((paragraph, index) => (
          <p key={index} className="text-sm leading-7 text-zinc-800 dark:text-zinc-200">
            {highlightSegments(paragraph).map((seg, i) =>
              seg.highlight ? (
                <span key={i} className="font-semibold text-orange-600 dark:text-orange-400">{seg.text}</span>
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
