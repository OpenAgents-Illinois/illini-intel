export function buildPredictionSummary(content: string, winProbability: number | null) {
  if (winProbability === null) return content;

  const probabilityText = `Illinois has a ${Math.round(winProbability)}% win probability.`;
  const normalizedContent = content.trim();

  if (!normalizedContent) return probabilityText;

  return `${probabilityText} ${normalizedContent}`;
}
