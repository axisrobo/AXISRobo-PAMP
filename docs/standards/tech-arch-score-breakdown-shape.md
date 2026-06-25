# Tech Architecture Score Breakdown Shape

## Problem
Technical Architecture AI results now use `score_breakdown` entries shaped as `{ score, max }`. Older UI code in some pages still assumed `score_breakdown` was `Record<string, number>` and multiplied values with hardcoded factors. That causes `NaN` bars and empty radar charts when the new payload is rendered.

## Rule
Always normalize Technical Architecture `score_breakdown` per dimension before rendering. Treat each dimension as an object with `score` and `max`, and compute radar/bar ratios with `score / max`.

## Fix Pattern
```tsx
const dimensionMaxMap: Record<string, number> = {
  connectivity: 1,
  security_compliance: 2,
  terminology_expression: 1,
  interaction_integration: 2,
  cloud_network_completeness: 2,
  technical_component_completeness: 2,
};

const normalizeDimension = (key: string, value: any) => {
  const normalizedKey = String(key).toLowerCase().replace(/\s+/g, '_');
  const fallbackMax = dimensionMaxMap[normalizedKey] ?? 1;
  if (typeof value === 'number') {
    return { score: Number(value) || 0, max: fallbackMax };
  }
  return {
    score: Number(value?.score ?? 0),
    max: Number(value?.max ?? fallbackMax),
  };
};

const ratio = dimension.max > 0 ? dimension.score / dimension.max : 0;
```

## Anti-pattern
```tsx
const scoreEntries = Object.entries(aiDetail.score_breakdown) as [string, number][];
const scaled = Number(val) * 5;
```