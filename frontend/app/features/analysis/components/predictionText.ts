export function buildPredictionSummary(content: string, winProbability: number | null, teamAName = "Team A") {
  if (winProbability === null) return content;

  const probabilityText = `${teamAName} has a ${Math.round(winProbability)}% win probability.`;
  const normalizedContent = content.trim();

  if (!normalizedContent) return probabilityText;

  return `${probabilityText} ${normalizedContent}`;
}
