# AVDM Scoring and Rule Configuration

Reference for the AVDM (Architecture Viewpoint Decision Model) concern catalog,
activation rules, and classification policy. The authoritative data lives in
`docs/SQL/avdm_config.json` and `docs/SQL/avdm_concerns_rules_seed.sql`, applied
by `scripts/db/init_db.py` after the base seed.

## Scoring

Every mapping and activation-rule contribution uses a defined **0-5 scale**:

| Value | Meaning |
|------:|---------|
| 1 | minor |
| 2 | low |
| 3 | moderate |
| 4 | high |
| 5 | critical |

For each concern, contributions are aggregated as **strongest signal plus a
small bonus per extra contributor** (not a sum), then mapped to `[0,1]`:

```
contribs = [c1, c2, ...] each in 0..5
aggregated = min(5, max(contribs) + 0.25 * (len(contribs) - 1))

aggregated = 0 : score = 0.0                                  -> Optional
aggregated > 0 : score = min(1, round(aggregated / 5 + complexityCoefficient * complexity, 4))
```

* `complexityCoefficient` default `0.15`; `complexity` is normalised to `[0,1]`.
* Classification thresholds: `Mandatory >= 0.90`, `Recommended >= 0.50`,
  otherwise `Optional`. On the 0-5 scale this means a single `5` is Mandatory,
  a single `3-4` is Recommended, and `1-2` is Optional (modulo the complexity
  boost).
* Aggregating by max+bonus prevents several weak mappings from accumulating
  into a false Mandatory; the previous plain sum did exactly that.
* The mapping is **continuous and floor-zero**: the previous `ceil(sqrt())`
  risk-level transform produced only nine distinct base values
  (`0.04 … 1.0`), which quantised classifications into coarse bands. The
  continuous form removes that artefact.
* An unactivated concern scores exactly `0.0`; the complexity boost is not
  applied, so empty inputs cannot manufacture priority.

Frontend and backend both implement this: `riskLevelsFromScore` in
`frontend/src/app/(architecture_review)/ea-review/(standalone)/request/create/page.tsx`
emits `severity = likelihood = sqrt(min(25, raw))`, and `evaluate_avdm` in
`backend/app/add/service.py` applies the floor and boost. The public analysis
mirrors it in `scripts/analysis/run_sensitivity.py`.

## Activation channels

1. **Question → concern mappings** (`avdm_question_answer_concern_mapping`):
   `match_operator` / `answer_value` against an answered question.
2. **Activation rules** (`avdm_concern_activation_rule` + `_score`): an `all`
   condition list (every condition must match) AND an `any` condition list (at
   least one must match). Condition sources:
   `question.<n>.answer`, `complexitySection.*`, `projectScaleSection.*`,
   `checkpoint1..3.*`, and `architectureTypeSection.*`.

### Question mapping model and UI maintenance

Mappings are stored as one row per `(question, answer, concern)` with a
`mapping_score` on the 0-5 scale. Every question has a **fixed concern set
across all of its answers**; an answer only changes the score. The admin editor
(`/concern-mapping-config` → **Edit Question Mapping**) presents this as a
**concern × answer matrix**: concerns are the rows, the question's answer
options are the columns, and each cell holds a score.

Workflow:

1. Pick the question; its answer options become the columns automatically.
2. Add the concerns this question contributes to. The concern set is defined
   once and shared by every answer, so adding/removing a concern changes all
   answers together.
3. Fill scores per cell. Most questions use one score across a row; per-cell
   scores are allowed where a concern needs a different weight (for example
   Q1, Q2, Q11, Q22, Q51, Q63, Q67).
4. **Save New Version** expands the matrix back into `(question, answer,
   concern)` rows. The stored representation is unchanged, so the analysis and
   fixtures are unaffected by the editor.

Scale questions (PS1, PS3, CS2, CS3, TCP1–TCP5) use banded scores: the lowest
band scores `2` (low) and higher bands score `3` (moderate). A critical single
signal such as cross-border data (TCP3) scores `5`. Redundant presence
questions CS1 and PS2 were removed in favour of the corresponding count
questions.

### Complexity drivers (RCP / SCP / PRS)

The requirement-, solution-, and resource-complexity matrices (stable ids
55-69) are **complexity drivers, not concern activations**. They use four
graded levels `None / Low / Medium / High` mapped to `0 / 2 / 4 / 6`, and their
selected scores are summed into the **derived project complexity**
(`requirementComplexitySection`, `solutionComplexitySection`,
`resourceSizeSection`; frontend `derivedProjectComplexity`). They have **no
question→concern mappings**.

### Architecture type rules

The 30 `at-*` rules key on `architectureTypeSection.<...>`. That section is
defined in `backend/app/add/questionnaire_config.py` and the frontend
`questionnaireConfig.ts`, and is a multiselect section. Those rules fire **only
when the assessment supplies architecture-type selections**; they are not dead,
but they do not fire for inputs (such as the constructed Case X benchmark) that
omit the section.

## Concern catalog

* Canonical keys are **code keys** (`A1`, `SCR7`, `DIN1`, …).
* 68 concerns total: 61 active, 7 inactive (`D12, D13, OR6, OR7, SCR8, SCR9,
  SCR10`).
* Legacy identifiers are aliases only: slug ids (`app_domain_boundary`,
  `security_identity_access`, …) → code keys, and `DIP7`/`DIP8` → `DIN1`/`DIN2`.
  The alias table is in `avdm_config.json` (`concerns[].aliases`) and documented
  in the public fixture README.
* `risk_tags` are intentionally empty: activation is driven by mappings and
  rules only, so no dilution from non-matching semantic tags.

Runtime uses the database catalog (`list_concerns(..., include_inactive=False)`).
The static `backend/app/add/catalog.py` is no longer used as an evaluation
fallback; an empty database catalog returns HTTP 503 so misconfiguration is
explicit rather than silently scored against a stale in-code catalog.

### Known semantic overlaps (kept for expert-study comparability)

`DIN5`↔`OR2`, `DIN6`↔`DIN4`, `IP7`↔`IP5/IP6`, `IP8`↔`IP2/A3`, `SCR11`↔`SCR6`,
`AGD1`↔`AGD7`. The expert study is fixed at 61 items, so these are retained
rather than merged.

## Case X calibration note

The constructed Case X benchmark was produced by an earlier configuration whose
question→concern associations and mapping scores are not fully present in the
base seed. To keep the benchmark reproducible, `avdm_config.json` restores:

* 10 associations (activation set): `AGD3, C5, D7, D9, IP1, IP2, OR1, OR4,
  SCR1, SCR7`;
* 8 score restorations: `A1, A2, A3, C1, C2, C3, C4` (+8 each) and `AGD2`
  (+16).

These are benchmark-fitting entries and are listed in
`avdm_config.json` → `generation_notes`.
