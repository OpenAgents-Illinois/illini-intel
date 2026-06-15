import { TeamHeader } from "@/app/features/analysis/components/TeamHeader";
import { WinProbability } from "@/app/features/analysis/components/WinProbability";
import { StatComparisonChart } from "@/app/features/analysis/components/StatComparisonChart";
import { ReportCardGrid } from "@/app/features/analysis/components/ReportCardGrid";
import { MatchupPreview } from "@/app/features/analysis/components/MatchupPreview";
import { Prediction } from "@/app/features/analysis/components/Prediction";
import { InsightCard } from "@/app/features/analysis/components/InsightCard";
import { KeyFactors } from "@/app/features/analysis/components/KeyFactors";
import { StreamState } from "@/app/features/analysis/types";

interface BiReportPanelProps {
  streamState: StreamState;
}

export function BiReportPanel({ streamState }: BiReportPanelProps) {
  const header = streamState.teamHeader;
  const teamAName = header?.team_a_name;
  const teamBName = header?.team_b_name;
  const teamAColor = header?.team_a_color;
  const teamBColor = header?.team_b_color;

  const hasOutput =
    streamState.teamHeader !== null ||
    streamState.winProbability !== null ||
    streamState.statComparisons.length > 0 ||
    streamState.reportCards.length > 0 ||
    streamState.matchupPreview !== null ||
    streamState.prediction !== null ||
    streamState.insightCards.length > 0 ||
    streamState.keyFactors.length > 0;

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
          teamAProbability={streamState.winProbability}
          teamAName={teamAName}
          teamBName={teamBName}
          teamAColor={teamAColor}
          teamBColor={teamBColor}
        />
      )}

      {streamState.prediction !== null && (
        <Prediction
          content={streamState.prediction}
          winProbability={streamState.winProbability}
          teamAName={teamAName}
        />
      )}

      {(!streamState.running || streamState.statComparisons.length > 0) && streamState.winProbability !== null && (
        <StatComparisonChart
          comparisons={streamState.statComparisons}
          teamAName={teamAName}
          teamBName={teamBName}
          teamAColor={teamAColor}
          teamBColor={teamBColor}
        />
      )}

      {streamState.keyFactors.length > 0 && (
        <KeyFactors
          factors={streamState.keyFactors}
          teamAName={teamAName}
          teamBName={teamBName}
          teamAColor={teamAColor}
          teamBColor={teamBColor}
        />
      )}

      {streamState.reportCards.length > 0 && (
        <ReportCardGrid cards={streamState.reportCards} teamAName={teamAName} teamBName={teamBName} />
      )}

      {streamState.insightCards.map((card, i) => (
        <InsightCard key={i} title={card.title} data={card.data} />
      ))}

      {streamState.matchupPreview !== null && <MatchupPreview content={streamState.matchupPreview} />}
    </div>
  );
}
