"use client";

import { useCallback, useState } from "react";
import { applyEvent, initialStreamState } from "@/app/features/analysis/state";
import { AgentEvent, StreamState } from "@/app/features/analysis/types";

interface UseAgentStreamProps {
  onStateChange: (state: StreamState) => void;
}

export function useAgentStream({ onStateChange }: UseAgentStreamProps) {
  const [state, setState] = useState<StreamState>(initialStreamState);

  const start = useCallback(
    (goal: string) => {
      const nextState: StreamState = { ...initialStreamState, running: true };
      setState(nextState);
      onStateChange(nextState);

      const url =
        (process.env.NEXT_PUBLIC_API_GATEWAY_URL ?? "") +
        "/analyze?goal=" +
        encodeURIComponent(goal);

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
