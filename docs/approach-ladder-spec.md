# Approach Ladder & Green Zone — feature spec

*Status: approved 2026-09-18. This is the agent crew's first job: architect refines the
plan from this spec, builder implements, test-runner gates. Every definition below was
validated against real data in the 2026-09-18 session (last-3-months window, n=396
approaches 60–170y) — do not re-litigate the definitions, do re-verify the numbers.*

## Why
Approach play into the green is the #1 measured leak (worst SG buckets; Green Zone %
~31 vs Broadie Am-bracket green rates; scramble ~6% makes every missed zone ≈ +0.5 to
+1.0 strokes). Garmin's on-green flag undersells reality by ~8 points (fringe/apron).

## Definitions (locked)
- **Green Zone (per approach shot):** `end_lie = 'Green' OR leave ≤ 15y OR holed`.
  Geometric and deterministic. The 15y radius is behaviorally validated: putter-next
  (by club, catching fringe putts) scores 31.3% vs zone15's 30.8%, and the median
  fringe-putt leave is 14.1y — the player's own putter choice draws the 15y circle.
  Putter-next is kept as a DIAGNOSTIC column only, never the definition (club choice
  drifts with confidence — see 2026-09-11 H16).
- **Rings:** ≤10y ("putt look") and ≤15y (the zone). No tighter than 10y (GPS noise
  5–10y). Pin-centered via canon.hole pin coords; holes without pins (≈16%) are
  excluded from ring math and counted in coverage badges.
- **Payoff anchors (computed, never hardcoded):** avg strokes-to-finish by leave class
  {green-putted, fringe/apron-putted, ≤15y chipped, 15–25y, 25y+}. 3-month reference
  values from the design session: 2.28 / 2.62 / 2.50 / 3.01 / 3.40.
- **Window:** last 90 days (config-tunable). Rationale: the 112-era golfer is not the
  same golfer; all-time pollutes. All ladder stats use this window; n badges always on.
- **Bins:** display bins 60-80 / 80-100 / 100-125 / 125-150 / 150-170 (config-driven
  edges), with 10y detail bins behind tap/expand. Per-club rows within a bin at n≥5.
- **Naming: NEVER call any of this GIR.** Garmin GIR stays untouched everywhere it
  already appears. New metric label: "Green Zone %" with scope suffix
  ("60–170y · last 3 mo · n=…"). Interpretability bar applies in full.

## Placement (locked — respect the busy-ness constraint: absorb, don't add)
1. ONE new card on the Insights tab: "Approach Ladder" — horizontal heat strip 60→170
   colored by Green Zone %, tap a bin → anatomy (n, median leave, short/long/right/left,
   from-lie mix, per-club rows). Payoff legend as one line under the strip.
2. ONE new priority metric: "Green Zone % (60–170y)" with trend + n badge. Nothing else
   new outside the card.
3. Bin-level findings (e.g. "PW at 120: 67% right — club up") flow through the EXISTING
   insight-card ranking so they surface only when they rank. No standing list.
4. Clubs tab keeps distances/dispersion; the ladder card owns the approach narrative.
5. Coach: a deterministic ladder block (season strip + this round's approaches in each
   bin, mirroring the benchmark round-samples pattern) so prescriptions can cite bins
   and the adherence loop can grade them.

## Findings to preserve as first insight evidence (verify against current data at build)
- Reach-swing signature: a club at/past stock max spikes short%+right% together —
  PW@120: 33% zone, 67% right (n=15); 7i@150: 25% zone, 88% short, 31y median leave.
- The cliff starts at 150 (not 160): zone 27%→10% across 150–170.
- 110–120 is the mid-range hole (~27–29% zone); 100y is the best window (50%).

## Architecture rules
- Derived layer only (SQL view derived.approach_ladder or insights.py compute —
  architect's call); constants/config per house convention; no schema change to canon.
- Tests on the fixture round + pure-function tests for binning/zone classification.
- Verification gate: pytest green, ruff clean, tools/parity clean, `update --no-pull`
  end-to-end with explainable processed diff, site renders the card (headless Chrome
  min-width ~500px quirk — verify at 500px+), coach context.md contains the block.
