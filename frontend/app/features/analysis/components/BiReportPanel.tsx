import { TeamHeader } from "@/app/features/analysis/components/TeamHeader";
import { WinProbability } from "@/app/features/analysis/components/WinProbability";
import { StatComparisonChart } from "@/app/features/analysis/components/StatComparisonChart";
import { ReportCardGrid } from "@/app/features/analysis/components/ReportCardGrid";
import { MatchupPreview } from "@/app/features/analysis/components/MatchupPreview";
import { Prediction } from "@/app/features/analysis/components/Prediction";
import { InsightCard } from "@/app/features/analysis/components/InsightCard";
import { KeyFactors } from "@/app/features/analysis/components/KeyFactors";
import { GroupedBarChart } from "@/app/features/analysis/components/GroupedBarChart";
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
    streamState.prediction !== null ||
    streamState.insightCards.length > 0 ||
    streamState.keyFactors.length > 0 ||
    streamState.charts.length > 0;

  return (
    <div className="w-1/2 overflow-y-auto p-4 space-y-4">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">BI Report</p>

      {!hasOutput && !streamState.running && (
        <p className="text-sm text-zinc-600">Insights will appear here as they arrive.</p>
      )}

      {streamState.teamHeader !== null && (
        <TeamHeader
          data={streamState.teamHeader}
          running={streamState.running}
          recentForms={streamState.recentForms}
        />
      )}

      {streamState.winProbability !== null && (
        <WinProbability
          probability={streamState.winProbability}
          opponentName={streamState.teamHeader?.opponent_name}
          opponentColor={streamState.teamHeader?.opponent_color}
        />
      )}

      {streamState.prediction !== null && (
        <Prediction content={streamState.prediction} winProbability={streamState.winProbability} />
      )}

      {(!streamState.running || streamState.statComparisons.length > 0) && streamState.winProbability !== null && (
        <StatComparisonChart
          comparisons={streamState.statComparisons}
          opponentName={streamState.teamHeader?.opponent_name}
          opponentColor={streamState.teamHeader?.opponent_color}
        />
      )}

      {streamState.keyFactors.length > 0 && (
        <KeyFactors
          factors={streamState.keyFactors}
          opponentName={streamState.teamHeader?.opponent_name}
          opponentColor={streamState.teamHeader?.opponent_color}
        />
      )}

      {streamState.reportCards.length > 0 && (
        <ReportCardGrid cards={streamState.reportCards} />
      )}

      {streamState.insightCards.map((card, i) => (
        <InsightCard key={i} title={card.title} data={card.data} />
      ))}

      {streamState.matchupPreview !== null && <MatchupPreview content={streamState.matchupPreview} />}
    </div>
  );
}
