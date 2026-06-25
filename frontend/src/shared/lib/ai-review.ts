export function getAiOverallScore(aiDetail: any): number {
  const overallScore = aiDetail?.overall_evaluation?.score;
  if (overallScore !== undefined && overallScore !== null && String(overallScore).trim() !== '') {
    const explicitScore = Number(overallScore);
    return Number.isFinite(explicitScore) ? explicitScore : 0;
  }

  const rootScore = aiDetail?.score;
  if (rootScore !== undefined && rootScore !== null && String(rootScore).trim() !== '') {
    const explicitScore = Number(rootScore);
    return Number.isFinite(explicitScore) ? explicitScore : 0;
  }

  return 0;
}

export function formatAiScoreDimensionLabel(key: string): string {
  const words = String(key)
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .split(/[_\s-]+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.toLowerCase());

  if (words.length === 0) {
    return '';
  }

  return words
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}