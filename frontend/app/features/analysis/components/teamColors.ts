export interface TeamColors {
  primary: string;
  secondary: string;
  accentText: string;
  accentSoft: string;
}

// Neutral side defaults, used only when ESPN provides no team color.
const DEFAULT_A: TeamColors = {
  primary: "#ff5f05",
  secondary: "#ff9b66",
  accentText: "#ff9b66",
  accentSoft: "rgba(255, 95, 5, 0.18)",
};

const DEFAULT_B: TeamColors = {
  primary: "#2563eb",
  secondary: "#93c5fd",
  accentText: "#93c5fd",
  accentSoft: "rgba(37, 99, 235, 0.18)",
};

export function getTeamColors(espnHex?: string, side: "a" | "b" = "a"): TeamColors {
  if (espnHex) {
    const hex = espnHex.startsWith("#") ? espnHex : `#${espnHex}`;
    return { primary: hex, secondary: hex, accentText: hex, accentSoft: `${hex}30` };
  }
  return side === "a" ? DEFAULT_A : DEFAULT_B;
}
