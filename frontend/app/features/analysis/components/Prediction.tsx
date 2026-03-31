interface PredictionProps {
  content: string;
}

export function Prediction({ content }: PredictionProps) {
  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/30">
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400">
        Prediction
      </h3>
      <p className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">{content}</p>
    </div>
  );
}
