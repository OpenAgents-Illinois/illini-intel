import { TeamHeader } from "@/app/features/analysis/components/TeamHeader";
import { WinProbability } from "@/app/features/analysis/components/WinProbability";
import { StatComparisonChart } from "@/app/features/analysis/components/StatComparisonChart";
import { ReportCardGrid } from "@/app/features/analysis/components/ReportCardGrid";
import { MatchupPreview } from "@/app/features/analysis/components/MatchupPreview";
import { Prediction } from "@/app/features/analysis/components/Prediction";
import { StreamState } from "@/app/features/analysis/types";

interface BiReportPanelProps {
  streamState: StreamState;
}

export function BiReportPanel({ streamState }: BiReportPanelProps) {
  const hasOutput =
    streamState.teamHeader !== null ||
    streamState.winProbability !== null ||
    streamState.statComparisons.length > 0 ||
    streamState.reportCards.length > 0 ||
    streamState.matchupPreview !== null ||
    streamState.prediction !== null;

  return (
    <div className="w-1/2 overflow-y-auto p-4 space-y-4">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">BI Report</p>

      {!hasOutput && !streamState.running && (
        <p className="text-sm text-zinc-600">Insights will appear here as they arrive.</p>
      )}

      {streamState.teamHeader !== null && (
        <TeamHeader data={streamState.teamHeader} running={streamState.running} />
      )}

      {streamState.winProbability !== null && (
        <WinProbability probability={streamState.winProbability} />
      )}

      {streamState.statComparisons.length > 0 && (
        <StatComparisonChart comparisons={streamState.statComparisons} />
      )}

      {streamState.reportCards.length > 0 && (
        <ReportCardGrid cards={streamState.reportCards} />
      )}

      {streamState.matchupPreview !== null && <MatchupPreview content={streamState.matchupPreview} />}
      {streamState.prediction !== null && <Prediction content={streamState.prediction} />}
    </div>
  );
}
