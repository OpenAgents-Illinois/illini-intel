"use client";

import { useEffect, useState } from "react";
import { MatchupSelection } from "@/app/features/analysis/hooks/useAgentStream";

interface LeagueOption {
  key: string;
  label: string;
  sport: string;
}

interface TeamOption {
  id: string;
  name: string;
}

interface MatchupSelectorProps {
  disabled?: boolean;
  onChange: (selection: MatchupSelection) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL ?? "";
const DEFAULT_LEAGUE = "mens-college-basketball";
const DEFAULT_TEAM_A = "356"; // Illinois
const DEFAULT_TEAM_B = "41"; // UConn

const SELECT_CLASS =
  "rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50";

export function MatchupSelector({ disabled = false, onChange }: MatchupSelectorProps) {
  const [leagues, setLeagues] = useState<LeagueOption[]>([]);
  const [teams, setTeams] = useState<TeamOption[]>([]);
  const [league, setLeague] = useState(DEFAULT_LEAGUE);
  const [teamA, setTeamA] = useState(DEFAULT_TEAM_A);
  const [teamB, setTeamB] = useState(DEFAULT_TEAM_B);

  // Load the league list once.
  useEffect(() => {
    fetch(`${API_BASE}/leagues`)
      .then((response) => response.json())
      .then((data: LeagueOption[]) => {
        if (Array.isArray(data) && data.length > 0) setLeagues(data);
      })
      .catch(() => {});
  }, []);

  // Load this league's teams whenever the league changes, resetting selections to valid ids.
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/teams?league=${encodeURIComponent(league)}`)
      .then((response) => response.json())
      .then((data: TeamOption[]) => {
        if (cancelled || !Array.isArray(data)) return;
        setTeams(data);
        setTeamA((prevA) => {
          const keepA = data.some((t) => t.id === prevA) ? prevA : data[0]?.id ?? "";
          setTeamB((prevB) => {
            if (data.some((t) => t.id === prevB) && prevB !== keepA) return prevB;
            return data.find((t) => t.id !== keepA)?.id ?? "";
          });
          return keepA;
        });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [league]);

  // Bubble the current selection up to the parent.
  useEffect(() => {
    onChange({ league, teamA, teamB });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [league, teamA, teamB]);

  return (
    <div className="flex items-center gap-2">
      <select
        className={SELECT_CLASS}
        value={league}
        disabled={disabled}
        onChange={(event) => setLeague(event.target.value)}
        aria-label="League"
      >
        {leagues.length === 0 && <option value={DEFAULT_LEAGUE}>NCAA Men&apos;s Basketball</option>}
        {leagues.map((option) => (
          <option key={option.key} value={option.key}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        className={SELECT_CLASS}
        value={teamA}
        disabled={disabled}
        onChange={(event) => setTeamA(event.target.value)}
        aria-label="Team A"
      >
        {teams
          .filter((team) => team.id !== teamB)
          .map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
      </select>

      <span className="text-xs text-zinc-500">vs</span>

      <select
        className={SELECT_CLASS}
        value={teamB}
        disabled={disabled}
        onChange={(event) => setTeamB(event.target.value)}
        aria-label="Team B"
      >
        {teams
          .filter((team) => team.id !== teamA)
          .map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
      </select>
    </div>
  );
}
