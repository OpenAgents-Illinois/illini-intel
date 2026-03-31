import { RecentFormItem } from "@/app/features/analysis/types";

interface RecentFormProps {
  forms: RecentFormItem[];
}

export function RecentForm({ forms }: RecentFormProps) {
  if (forms.length === 0) return null;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Recent Form</div>
      <div className="flex flex-col gap-3">
        {forms.map((form) => (
          <div key={form.team} className="flex items-center gap-3">
            <span className="text-xs text-zinc-400 w-20 shrink-0 text-right truncate">{form.team}</span>
            <div className="flex gap-1.5">
              {form.results.length === 0 ? (
                <span className="text-xs text-zinc-600">No data</span>
              ) : (
                form.results.map((result, i) => (
                  <div
                    key={i}
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold ${
                      result === "W" ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
                    }`}
                  >
                    {result}
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
