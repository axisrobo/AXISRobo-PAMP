export function aggregateConcernScores(scores: number[]): number {
  if (scores.length === 0) return 0;
  const normalized = scores.map((score) => Math.min(5, Math.max(0, score)));
  return Math.min(5, Math.max(...normalized) + 0.25 * (normalized.length - 1));
}
