"use client";

import { useCallback, useState } from "react";
import { AgentTracePanel } from "@/app/features/analysis/components/AgentTracePanel";
import { BiReportPanel } from "@/app/features/analysis/components/BiReportPanel";
import { useAgentStream } from "@/app/features/analysis/hooks/useAgentStream";
import { initialStreamState } from "@/app/features/analysis/state";
import { StreamState } from "@/app/features/analysis/types";

const DEFAULT_GOAL = "Analyze Illinois vs UConn Final Four matchup";

export function AnalysisPage() {
  const [goal, setGoal] = useState(DEFAULT_GOAL);
  const [streamState, setStreamState] = useState<StreamState>(initialStreamState);
  const { start } = useAgentStream({ onStateChange: setStreamState });

  const handleRun = useCallback(() => {
    if (!streamState.running) {
      start(goal);
    }
  }, [goal, start, streamState.running]);

  return (
    <div className="min-h-screen bg-zinc-950 font-sans text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Illini Intel</h1>
          <p className="text-xs text-zinc-500">Fighting Illini Basketball BI</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            className="w-80 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:border-orange-500 focus:outline-none"
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="Ask about Illinois basketball..."
            disabled={streamState.running}
          />
          <button
            onClick={handleRun}
            disabled={streamState.running}
            className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-50"
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
