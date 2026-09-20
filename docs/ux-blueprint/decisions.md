# UX Blueprint — running decisions log

*Interactive design phase (roadmap job 2), Colby + Claude. Locked decisions accumulate
here; per-screen data contracts and the component inventory are written at the end.
Live mock: the "My Game Concept" artifact (session-published; iterated in place).*

## Locked (as of 2026-09-19)
- Top-level nav: Home · Progress · My Game · Rounds · Practice("soon") — bottom bar,
  thumb-first; no swiping BETWEEN top-level tabs.
- Mobile-first: phone is a first-class citizen; web = expansion of the phone layout;
  everything must survive a later Capacitor wrap unchanged.
- "Now" vs "Growth" split: Home answers "where do I stand now / what do I work on";
  Progress consolidates ALL improvement views (today's home improvement chart + the
  performance cone) into one page.
- My Game = domain-card stack (Approach, Off the Tee, Short Game, Putting, Sequences,
  Strokes Gained, Clubs), ordered by the KPI charter's stage priorities, FOCUS badge
  on active priorities. Card anatomy: verdict line + mini-viz (7-rung ladder) +
  coverage badges. Density as mocked; tap = drill.
- Drill = full-screen; swipe left/right between SIBLING domains (charter order),
  page dots; horizontal-scrolling content owns its gesture; Rounds later inherits
  swipe = previous round.
- Approach drill layout (per concept image, validated on real data): verdict →
  Green Zone performance grouped bars (GZ% + on-green% pairs, values on bars, n under
  bins) → "Where you miss" with BAND CHIPS (60–100 / 100–150 / 150+ / All; segmented
  control, not a slider) recomputing direction rows + shot scatter client-side →
  key-insight callout → payoff strip.
- Aesthetic: concept-image discipline. Warm off-white ground / white cards / hairline
  borders / 8px radii / one green (forest) + semantic red for misses / Archivo,
  tabular-nums / both themes deliberately designed. Data text >= ~11px — small chart
  type reads as mid on phones.

## SG backbone principle (locked 2026-09-19, Colby reading Every Shot Counts)
Strokes Gained is the interpreted SOURCE OF TRUTH; The Turn's constructs are its
mechanism layer, and every construct reconciles to it:
- Every My Game domain card carries its SG/round in the verdict line — the card stack
  visibly sums to the score. The SG drill = the full accounting view (5-bucket
  decomposition, trends, cross-category scatters).
- Home focus areas are PRICED IN STROKES from SG ("Approach 150+ ≈ 2.4 strokes/round")
  — SG is the common currency that makes priorities comparable.
- Graduation: stack metrics remain the trigger; the SG category move is the validator
  and is cited in the graduation evidence. Metric improves but SG doesn't move = flag,
  not graduation.
- Reliability guardrail stands: SG governs at category level over windows (off-tee /
  approach reliable; putting / inside-50 directional) — mechanism constructs are the
  noise-robust proxies that explain it. Payoff anchors are recognized as a personal
  expected-strokes function; awful shots = shot-value math; benchmark gaps are
  SG-denominated (Broadie Table 4).
- Positioning: same Broadie foundation as everyone; The Turn differentiates by saying
  what the SG means and what to do next (sequences, strategy, decisions — all priced
  in strokes as they arrive).

## Generalization requirements (multi-tenant correctness, locked 2026-09-19)
1. Bin edges are SHARED config for all players (never per-tenant — do-not-list rule);
   what personalizes is computed: default band chip = the player's own worst band
   ("cliff detector"), key insight = deterministic template over their joint miss
   distribution, verdict/strongest/weakest computed (already true in ladder.py).
2. Per-connector capability degradation: a hole-level source (18Birdies) renders the
   Approach card as green-hit-only with an explicit "no shot-level data" chip — no
   scatter, no leaves; the UI states what a shot-level source unlocks. Screens declare
   required capabilities in their data contracts.
3. Screen data contracts carry NO player specifics: e.g. Approach drill consumes
   {bins, verdict, defaultBand, insight, missByBand, scatterShots, coverage} from the
   per-tenant pipeline run.

## Personal par / stroke budget (concept locked 2026-09-19; spec later with Rounds)
Colby's construct, arrived at via ESC: hole-level expectation adapted to level —
"at bogey golf a par 4 gives me 3 shots to the green; 5 is target hit."
- Personal par per hole = blend of the player's own course-ledger distribution (where
  history exists) with handicap stroke-index allocation (where it doesn't); stage-aware;
  deterministic. Watching a hole's personal par drop (H15: 6 → 5) IS progression.
- Budget view denominated in STROKES-OVER, not required putts (putt-debt framing
  implies putting must compensate → wrong prescription; contain, don't compensate).
  Target score = budget; rounds show burn vs budget; the putts version survives as
  post-round autopsy copy.
- Makes the coach's "play H5/H7 as bogey holes" prose structural: per-hole plans
  differ by stage (Colby Control: budget 5, layup; Steve Convert: budget 4.5, attack).
- Surfaces: Rounds (personal-par column, budget burn), course-strategy/pre-round view,
  Home round pulse ("beat your budget by 3"). All SG-priced per the backbone principle.

## Open (next screens to design)
- Home (stage banner + focus areas + latest-round pulse) — next up, or Progress.
- Progress/Growth consolidation layout.
- Rounds, Sequences drill, SG drill, Clubs drill; Practice placeholder content.
