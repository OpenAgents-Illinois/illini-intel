"use client";

import { useCallback, useState } from "react";
import { applyEvent, initialStreamState } from "@/app/features/analysis/state";
import { AgentEvent, StreamState } from "@/app/features/analysis/types";

interface UseAgentStreamProps {
  onStateChange: (state: StreamState) => void;
}

export interface MatchupSelection {
  league: string;
  teamA: string;
  teamB: string;
}

export function useAgentStream({ onStateChange }: UseAgentStreamProps) {
  const [state, setState] = useState<StreamState>(initialStreamState);

  const start = useCallback(
    (selection: MatchupSelection) => {
      const nextState: StreamState = { ...initialStreamState, running: true };
      setState(nextState);
      onStateChange(nextState);

      const base = process.env.NEXT_PUBLIC_API_GATEWAY_URL ?? "";
      const url =
        `${base}/analyze?league=${encodeURIComponent(selection.league)}` +
        `&team_a=${encodeURIComponent(selection.teamA)}` +
        `&team_b=${encodeURIComponent(selection.teamB)}`;

      const eventSource = new EventSource(url);

      eventSource.onmessage = (message) => {
        try {
          const event: AgentEvent = JSON.parse(message.data);
          setState((prevState) => {
            const updatedState = applyEvent(prevState, event);
            onStateChange(updatedState);
            return updatedState;
          });
          if (event.type === "done") {
            eventSource.close();
          }
        } catch {
          // Ignore malformed events from the stream.
        }
      };

      eventSource.onerror = () => {
        setState((prevState) => {
          const updatedState = { ...prevState, running: false, done: true };
          onStateChange(updatedState);
          return updatedState;
        });
        eventSource.close();
      };
    },
    [onStateChange]
  );

  return { state, start };
}
