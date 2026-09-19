# KPI Charter — tier-relative metrics with graduation

*Status: approved 2026-09-18. Crew job #2, after the approach ladder
(docs/approach-ladder-spec.md). The insight this encodes: first-class metrics are
TIER-RELATIVE — penalties/doubles are the 25→18 separators, green zone/approach the
18→12 separators, and a metric that is solved should stop shouting. The Turn should
know which 3-4 KPIs matter for the player's current level, headline only those, and
graduate them when they're sustained — no more stumbling onto the next lever.*

## The separator stack (encode as config, cite sources per entry)
Tier boundaries use the RATING-LEVELED scoring average (house rule — never raw scores;
see benchmarks.py `_scoring_level`), mapped where citable to Broadie's groups
(config/benchmarks_broadie.json) and Stagner population data.

- **T-25 ("stop losing strokes", adj avg ≥ 98):** penalties/18, doubles+/18, awful
  shots/18 (< -0.8, Broadie eq.), tee-ball playability %, 3-putt rate from 30+ ft.
- **T-18 ("gain positions", adj avg 90-98):** Green Zone % (60-170y), bogey conversion
  %, blow-up concentration, par-3 scoring split, wedge distance control (<100y).
- **T-12 (adj avg 84-90):** proximity tightening (median leave by band), up-and-down %,
  driver distance-vs-dispersion, par-5 scoring.
- **T-6 and better:** placeholder — document, don't build (no user at this tier yet).

A player's ACTIVE tier = where their adjusted average sits; first-class KPIs = the
active tier's list MINUS graduated metrics PLUS any re-promoted regressions.

## New metrics to build (v1 ships the first three — all scorecard/derived-only)
1. **Bogey conversion %** — of holes WITHOUT a GIR (authoritative hole_facts.gir),
   % scored bogey or better. Scorecard-only, all rounds (rate metric). Upgrade path
   (v1.1): green-zone-in-regulation variant once the ladder lands. Windows + n badges
   per house convention.
2. **Blow-up concentration** — per 18-hole regulation round: sum of the worst 3 holes'
   over-par ÷ total over-par (positive holes only), averaged over the window. The
   "is the floor structurally rising?" number. Regulation-only (distribution shape).
3. **Par-3 scoring split** — avg over-par and doubles% by hole par (3/4/5). Scorecard
   only. Surfaces the H10/H11-type leak class.
4. *(v1.1)* **Tee-ball playability %** — annotation-first (post_tee_state clean %),
   geometry proxy fallback for unannotated rounds (next shot advances normally, no
   recovery signature, no hole penalty) — proxy definition is the architect's call,
   coverage-badged, never silently mixed with the annotated version.
5. *(v1.1)* **Lag quality** — 3-putt rate on first putts ≥ 30 ft (bands data exists);
   leave-based upgrade only if putt-level geometry proves reliable (it is
   green-center-based — see known quirks).
6. *(v1.1)* **Wedge ladder 40-100y** — extend the approach ladder bins downward,
   same definitions, same card.

## Graduation rules (all thresholds in config with rationale strings)
- Each stack entry carries: `target`, `sustainRounds` (default 8 regulation rounds for
  scoring-scope metrics, 8 rounds any-scope for rates), `reentryThreshold`.
- **Graduate:** metric meets target across the sustain window → move from headline to
  watchlist row; auto-promote the next unsatisfied metric from the active tier (or the
  next tier if the active tier is clear).
- **Re-promote (hysteresis):** a graduated metric breaching `reentryThreshold` for 4+
  consecutive rounds returns to the headlines. Thresholds must differ from targets
  (no flapping).
- Every state change is an insight-card event with the evidence ("Penalties/18 held
  ≤1.0 for 8 rounds — graduated; Green Zone % promoted").

## Presentation (this REPLACES the current priority-metrics presentation — absorb)
- **Headline strip:** the 3-4 active first-class KPIs — value, target, trend arrow,
  n badge, one scope suffix each. Tier shown once ("18→12 track"), plain words.
- **Watchlist:** graduated metrics as compact single rows (value + quiet target check).
- **Coach:** a charter block — active KPIs with status, recent graduations/regressions
  — so prescriptions align with the active stack, and the adherence loop grades against
  it. Insight ranking gets a weight bonus for findings touching active KPIs.
- Interpretability bar in full: plain-word labels, one scope per line, "was it good?"
  answerable per KPI via its target.

## Multi-tenant note (vNext2)
Tier derivation is automatic per tenant (adjusted average); the stack/config is SHARED
math — tenant config selects nothing (see vNext2 do-not list: customization must not
fork analytics definitions). Steve gets his tier's stack, not Colby's. This is a
candidate vNext2 flagship: "the metric that matters now."

## Architecture + gate
Derived layer + config only; no canon changes. Charter state (graduation history) is
derived from round data + config thresholds — recomputable, never stored as unique
state. Tests: tier assignment, graduation/hysteresis transitions (pure functions),
metric math on the fixture round. Gate: pytest, ruff, parity, `update --no-pull`
end-to-end, site headline strip renders (≥500px), coach context contains the charter
block.
