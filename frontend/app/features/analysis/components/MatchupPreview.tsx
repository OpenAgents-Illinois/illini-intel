interface MatchupPreviewProps {
  content: string;
}

export function MatchupPreview({ content }: MatchupPreviewProps) {
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950/30">
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-400">
        Matchup Preview
      </h3>
      <p className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">{content}</p>
    </div>
  );
}
