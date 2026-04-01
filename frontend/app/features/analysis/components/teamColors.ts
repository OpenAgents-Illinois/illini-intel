export interface TeamColors {
  primary: string;
  secondary: string;
  accentText: string;
  accentSoft: string;
}

const TEAM_COLOR_MAP: Record<string, TeamColors> = {
  illinois: {
    primary: "#ff5f05",
    secondary: "#13294b",
    accentText: "#ff9b66",
    accentSoft: "rgba(255, 95, 5, 0.18)",
  },
  uconn: {
    primary: "#0c2340",
    secondary: "#6aa2ff",
    accentText: "#93c5fd",
    accentSoft: "rgba(106, 162, 255, 0.18)",
  },
  connecticut: {
    primary: "#0c2340",
    secondary: "#6aa2ff",
    accentText: "#93c5fd",
    accentSoft: "rgba(106, 162, 255, 0.18)",
  },
  purdue: {
    primary: "#cfb991",
    secondary: "#000000",
    accentText: "#f1ddb7",
    accentSoft: "rgba(207, 185, 145, 0.18)",
  },
  indiana: {
    primary: "#990000",
    secondary: "#f3f4f6",
    accentText: "#fca5a5",
    accentSoft: "rgba(153, 0, 0, 0.18)",
  },
  northwestern: {
    primary: "#4e2a84",
    secondary: "#b8a6d9",
    accentText: "#d8cced",
    accentSoft: "rgba(78, 42, 132, 0.18)",
  },
  michigan: {
    primary: "#ffcb05",
    secondary: "#00274c",
    accentText: "#fde68a",
    accentSoft: "rgba(255, 203, 5, 0.18)",
  },
  michiganstate: {
    primary: "#18453b",
    secondary: "#b2c7c2",
    accentText: "#bbf7d0",
    accentSoft: "rgba(24, 69, 59, 0.18)",
  },
  "michigan state": {
    primary: "#18453b",
    secondary: "#b2c7c2",
    accentText: "#bbf7d0",
    accentSoft: "rgba(24, 69, 59, 0.18)",
  },
  wisconsin: {
    primary: "#c5050c",
    secondary: "#f3f4f6",
    accentText: "#fca5a5",
    accentSoft: "rgba(197, 5, 12, 0.18)",
  },
  iowa: {
    primary: "#ffcd00",
    secondary: "#111111",
    accentText: "#fde68a",
    accentSoft: "rgba(255, 205, 0, 0.18)",
  },
  maryland: {
    primary: "#e03a3e",
    secondary: "#ffd520",
    accentText: "#fda4af",
    accentSoft: "rgba(224, 58, 62, 0.18)",
  },
  ohiostate: {
    primary: "#bb0000",
    secondary: "#cfd4d8",
    accentText: "#fca5a5",
    accentSoft: "rgba(187, 0, 0, 0.18)",
  },
  "ohio state": {
    primary: "#bb0000",
    secondary: "#cfd4d8",
    accentText: "#fca5a5",
    accentSoft: "rgba(187, 0, 0, 0.18)",
  },
};

const DEFAULT_OPPONENT_COLORS: TeamColors = {
  primary: "#2563eb",
  secondary: "#93c5fd",
  accentText: "#93c5fd",
  accentSoft: "rgba(37, 99, 235, 0.18)",
};

function normalizeKey(teamName: string) {
  return teamName.trim().toLowerCase().replace(/[^a-z0-9 ]/g, "");
}

export function getIllinoisColors(): TeamColors {
  return TEAM_COLOR_MAP.illinois;
}

export function getOpponentColors(teamName: string | undefined, espnHex?: string): TeamColors {
  if (!teamName) return DEFAULT_OPPONENT_COLORS;
  const normalized = normalizeKey(teamName);
  if (TEAM_COLOR_MAP[normalized]) return TEAM_COLOR_MAP[normalized];

  // Fall back to ESPN-sourced hex color if the team isn't in the static map
  if (espnHex) {
    const hex = espnHex.startsWith("#") ? espnHex : `#${espnHex}`;
    return {
      primary: hex,
      secondary: hex,
      accentText: hex,
      accentSoft: `${hex}30`,
    };
  }

  return DEFAULT_OPPONENT_COLORS;
}
