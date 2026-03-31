import { InsightCardItem } from "@/app/features/analysis/types";

export function InsightCard({ title, data }: InsightCardItem) {
  return (
    <div className="rounded-xl border border-orange-200 bg-orange-50 p-4 dark:border-orange-900 dark:bg-orange-950/30">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-orange-700 dark:text-orange-400">
        {title}
      </h3>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2">
        {Object.entries(data).map(([key, value]) => (
          <div key={key}>
            <dt className="text-xs text-zinc-500 dark:text-zinc-400">{key}</dt>
            <dd className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{String(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
