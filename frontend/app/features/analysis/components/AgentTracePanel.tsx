import { StreamState } from "@/app/features/analysis/types";

interface AgentTracePanelProps {
  streamState: StreamState;
}

export function AgentTracePanel({ streamState }: AgentTracePanelProps) {
  return (
    <div className="w-1/2 space-y-2 overflow-y-auto border-r border-zinc-800 p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
        Agent Trace
      </p>
      {streamState.thoughts.length === 0 && !streamState.running && (
        <p className="text-sm text-zinc-600">Run an analysis to see agent reasoning.</p>
      )}
      {streamState.thoughts.map((thought, index) => (
        <div key={index} className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
          <span className="mr-2 text-xs font-semibold uppercase text-orange-400">
            {thought.agent}
          </span>
          <span className="text-sm text-zinc-300">{thought.content}</span>
        </div>
      ))}
      {streamState.toolCalls.map((toolCall, index) => (
        <div key={`tool-call-${index}`} className="rounded-lg border border-zinc-700 bg-zinc-900 p-3">
          <span className="mr-2 text-xs font-semibold uppercase text-purple-400">
            {toolCall.agent} -&gt; {toolCall.tool}
          </span>
          <pre className="mt-1 overflow-x-auto text-xs text-zinc-500">
            {JSON.stringify(toolCall.args, null, 2)}
          </pre>
        </div>
      ))}
      {streamState.running && (
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-orange-500" />
          Agents running...
        </div>
      )}
      {streamState.done && <div className="pt-2 text-xs text-zinc-600">Analysis complete.</div>}
    </div>
  );
}
