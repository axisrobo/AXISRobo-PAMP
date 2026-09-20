import assert from 'node:assert/strict';
import test from 'node:test';

import { aggregateConcernScores } from './concernScoring.ts';

test('aggregates the strongest signal plus one bonus per extra contributor', () => {
  assert.equal(aggregateConcernScores([1, 1, 4]), 4.5);
  assert.equal(aggregateConcernScores([4, 1, 1]), 4.5);
});

test('handles empty, single, and capped aggregates', () => {
  assert.equal(aggregateConcernScores([]), 0);
  assert.equal(aggregateConcernScores([3]), 3);
  assert.equal(aggregateConcernScores([5, 5]), 5);
});
