"use client";

import { useCallback, useRef, useState } from "react";
import { AgentTracePanel } from "@/app/features/analysis/components/AgentTracePanel";
import { BiReportPanel } from "@/app/features/analysis/components/BiReportPanel";
import { MatchupSelector } from "@/app/features/analysis/components/MatchupSelector";
import { MatchupSelection, useAgentStream } from "@/app/features/analysis/hooks/useAgentStream";
import { initialStreamState } from "@/app/features/analysis/state";
import { StreamState } from "@/app/features/analysis/types";

const INITIAL_SELECTION: MatchupSelection = {
  league: "mens-college-basketball",
  teamA: "356",
  teamB: "41",
};

export function AnalysisPage() {
  const [streamState, setStreamState] = useState<StreamState>(initialStreamState);
  const selectionRef = useRef<MatchupSelection>(INITIAL_SELECTION);
  const { start } = useAgentStream({ onStateChange: setStreamState });

  const handleRun = useCallback(() => {
    if (streamState.running) return;
    const selection = selectionRef.current;
    if (selection.teamA && selection.teamB && selection.teamA !== selection.teamB) {
      start(selection);
    }
  }, [start, streamState.running]);

  return (
    <div className="min-h-screen bg-zinc-950 font-sans text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Matchup Intel</h1>
          <p className="text-xs text-zinc-500">Agentic team-vs-team sports BI</p>
        </div>
        <div className="flex items-center gap-3">
          <MatchupSelector
            disabled={streamState.running}
            onChange={(selection) => {
              selectionRef.current = selection;
            }}
          />
          <button
            onClick={handleRun}
            disabled={streamState.running}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {streamState.running ? "Running..." : "Run Analysis"}
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-65px)]">
        <AgentTracePanel streamState={streamState} />
        <BiReportPanel streamState={streamState} />
      </div>
    </div>
  );
}
