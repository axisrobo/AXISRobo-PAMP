# LLM JSON Output Hardening

## Problem
LLM responses may include extra text, markdown wrappers, or partial JSON (for example only score_breakdown), which can cause JSON parsing failures or schema validation errors and return 500.

## Rule
Always normalize LLM JSON output before strict schema validation.

## Fix Pattern
1. Extract JSON robustly:
- Prefer fenced ```json blocks.
- Otherwise decode the first valid JSON object from text.

2. Normalize result shape before validation:
- Ensure top-level fields exist: title, overall_evaluation, score_breakdown, issues, recommendations.
- Map aliases (overall -> overall_evaluation, related_relationshipes -> related_relationships when needed).
- Fill missing optional arrays with empty lists.
- Fill missing overall_evaluation with safe defaults.
- Treat overall_evaluation.score as authoritative when present; do not recompute or override it from score_breakdown.
- If the model returns only score_breakdown for architecture review, synthesize deterministic fallback issues/recommendations from low-score dimensions instead of returning empty arrays.

3. Validate with Pydantic only after normalization.

## Anti-pattern
- Directly parsing model text with json.loads on naive substring slices.
- Validating raw model output against strict schema without fallback normalization.
