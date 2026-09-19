# The Turn — Development Analytics Concept

*Source: Colby's product-direction notes, developed in conversation with ChatGPT,
delivered 2026-09-19 alongside the six-screen mockup (docs/assets/turn-concept.png).
Preserved as-received; the sequencing decisions and the mapping of these ideas onto
existing specs live in docs/roadmap.md.*

## Product Direction
The Turn should evolve from a golf statistics dashboard into a **player-development
and diagnostic system**. Strokes gained answers "Where did I lose strokes?" The Turn
should answer "What underlying patterns are causing those losses, what should I work
on at my current stage, and what evidence supports that conclusion?" SG remains the
measurement layer; differentiation comes from analyzing relationships between shots,
decisions, outcomes, and longer-term development.

## 1. Stage-Based Player Development
Golfers at different levels face different problem classes. Determine a development
stage and use it to prioritize analytics:
- **25+ — Stabilize:** penalties, triples+, basic playability
- **18-25 — Control:** doubles+, penalties, recovery, severe misses
- **10-18 — Convert:** bogey-to-par conversion, approach quality, Green Zone, scrambling
- **5-10 — Optimize:** proximity, par/birdie opportunities, scrambling efficiency, putting conversion
- **<5 — Refine:** increasingly granular optimization
Ranges/competencies should eventually be data-driven. Handicap identifies the stage;
progression should reflect whether the stage's skills have become RELIABLE. UI:
**Current Stage → Current Priorities → Established Skills → What's Next** — game-like
progression without overt gamification.

## 2. Outcomes vs. Root Causes
**A metric showing a weakness does not necessarily identify the thing to improve.**
Example: weak scrambling + putting may be downstream of: poor approach → missed Green
Zone → difficult scramble → long first putt → miss. Distinguish: **Outcome** (where
strokes were lost) / **Diagnosis** (what patterns produced it) / **Root constraint**
(most important upstream weakness) / **Prescription** (what to focus on). Continually
ask: "Is this metric the problem, or the consequence of an earlier problem?"

## 3. Shot Sequences as a Core Analytical Unit
Analyze **sequences**, with two-shot pairings as the atomic unit. A single shot
measures execution; two shots reveal what the golfer did with the situation the
previous shot created. (Driver → trees → lateral recovery, vs. driver → trees →
aggressive advancement → still in trouble: same first mistake, the second shot decides
whether it is contained or amplified.)
- **Mistake Amplification:** entering a disadvantaged position, how often does the
  next shot improve / maintain / worsen it?
- **Opportunity Conversion:** after a shot creates an advantage, how often does the
  next shot capitalize?
Higher handicaps benefit most from containment; lower handicaps from conversion.

## 4. Green Zone
Strict GIR is too binary for development analysis (1y onto fringe vs 35y short both
"missed"). **Green Zone = green + ~15y radius around the target.** Enables the
**Approach Ladder**: 10y distance buckets, each analyzed for Green Zone %, GIR %,
miss direction/severity, club, lie, subsequent shot, hole outcome. E.g. 80-100y >50%
Green Zone vs material drop at 140+ with short-right dominant — a far more specific
target than "Approach SG is weak."

## 5. Work Backward From Desired Outcomes
Start from desired states (par 4: tee → approach → Green Zone; par 5: tee →
advancement → approach → Green Zone) and ask which sequences reliably reach scoring
positions and which transitions break down. E.g. after tree trouble: lateral →
bogey-or-better strong; aggressive advancement → poor. Diagnosis: the miss costs, but
the RESPONSE to the miss disproportionately creates doubles.

## 6. AI Analytical Agents
Not stat-to-prose translation ("Approach SG -2.1 → practice irons" adds nothing).
Agents perform iterative investigation: Putting SG poor → why? long first putts →
why? scrambling → why? Green Zone misses → where? 140-180 → what miss? short-right →
varies by club/lie/prior shot? Conclusion: "Putting is losing strokes, but putting is
not the primary development constraint — approach from 140+ is creating the downstream
difficulty."

## 7. Evidence and Confidence
Insight evidence levels: **Strong Pattern** (repeated, meaningful sample) / **Emerging
Pattern** (needs more observations) / **Insufficient Evidence**. Be comfortable saying
"not enough reliable shots to conclude" — especially given third-party shot-data
quality.

## 8. Proposed Information Architecture
Progressively deeper, not everything at once:
- **Progress / Journey** — "Am I getting better?" Long-term scoring, stage progression,
  established skills, movement toward next stage.
- **My Game / Current Focus** — "What's holding me back?" ~3 priorities with concise
  evidence, plus improving/established areas.
- **Strokes Gained** — kept as diagnostic view, not the organizing concept.
- **Round Analysis / Coach** — the patterns that actually affected the score ("today's
  primary pattern was recovery-state management…"), not bucket totals.
- **Explore** — rounds, shots, maps, clubs as supporting evidence, lower in hierarchy.

## 9. Core Product Thesis
Differentiate on **diagnostic depth**, not stat volume:
**Statistics → Patterns → Sequences → Root Constraints → Development Priorities.**
> Don't treat every measurable weakness as an independent problem. Trace scoring
> outcomes backward through shot sequences to identify the smallest number of upstream
> patterns constraining the golfer's development.
Stage determines which outcomes matter; sequences and Green Zone determine why; AI
performs the deeper investigation. The result: a **longitudinal analytical coach that
increasingly understands how the individual golfer produces their scores.**
