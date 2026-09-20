# The Turn — philosophy and canon

*The durable statement of what this product believes and why its constructs exist.
This is the seed corpus for the Learn/help articles and eventually the blog: every
article is a retelling of a section here, in the same voice. The writer agent treats
this file as canon; changes to it are product decisions, not copy edits.*

## The thesis

Golf apps tell you what happened. The Turn is a **player-development system**: it
tells you why it happened, what to work on at your current stage, and whether you
actually did it. The test for every number on every screen is the same: can the
golfer answer **"was it good?"** at a glance, without a legend and without lying to
themselves?

## The lineage — and what's ours

- **Mark Broadie, *Every Shot Counts*** — the measurement. Strokes Gained values
  every shot against expectation; it's the moneyball of golf and the accounting
  truth underneath everything here.
- **Scott Fawcett, DECADE** — the prescription. Dispersion-first strategy,
  no hero pins, expectation management by level.
- **The Turn** — personalization with receipts. DECADE prescribes from tour
  dispersion; The Turn prescribes from YOUR measured dispersion, YOUR hole-by-hole
  ledger, YOUR miss patterns — and then the coach checks next round whether the
  prescription showed up, and says so. Nothing here is generic advice; every claim
  carries its sample size.

## Strokes Gained, in plain words (the backbone)

Every shot starts somewhere (a distance, a lie) and ends somewhere. From every
starting point there's an expected number of strokes to finish the hole. A shot
GAINS strokes when it beats that expectation and loses them when it doesn't. Add up
a round and you know exactly where the score came from — driving, approach, short
game, putting — with nothing hidden and nothing double-counted.

In The Turn, SG is the **scoreboard, not the language**. Every game area carries its
SG price; priorities are compared in strokes because strokes are the only common
currency; a skill only "graduates" when its SG category confirms the improvement.
But the golfer-facing words are mechanisms and targets, not SG jargon — you don't
need to understand the accounting to be coached by it. Honesty note: GPS-derived SG
is reliable for full shots, directional for putting and inside-50 — so SG governs at
the category level over windows, and the constructs below are the noise-robust
explanations underneath it.

## Green Zone — what it is and why we built it

**Green Zone = the approach finished on the green, inside 15 yards of the pin, or
in the hole.** It is deliberately not GIR.

Why: GIR is binary and blind. A ball one foot onto the fringe and a ball 35 yards
short are both "missed greens," yet they are different sports. Worse, sensor
platforms under-credit the fringe. When we tested definitions against real data,
three candidates converged: the geometric 15-yard ring, the golfer's own behavior
(the median off-green putt was chosen from 14.1 yards — the player's putter draws
the circle), and the payoff (finishing on the green costs ~2.2 more strokes to hole
out; inside 15 yards ~2.6; beyond 25 yards ~3.4). The ring is geometric and
deterministic; the behavior validated the radius; the payoff prices it. That's the
house method: define constructs by evidence, publish the validation, and never let
the new word blur into an old one (Garmin's GIR stays untouched, always).

## Personal par and the stroke budget

Par is the card's opinion. Your par is what YOUR level and YOUR history say a hole
should cost — at bogey golf, a par 4 gives you three shots to the green, and a 5 is
a target hit, not a failure. The Turn computes personal par per hole (your own
scoring history where it exists, handicap allocation where it doesn't), turns a
target score into a per-hole stroke budget, and reports rounds as budget burn.
Progression becomes visible hole by hole: the day H15 stops being a 6 for you is
the day you got better, whatever the card says. Budgets are denominated in strokes,
never in "required putts" — when the long game overspends, the fix is containment,
not compensating heroics on the green.

## Stages and graduation — the metric that matters now

Different levels have different problems. Penalties and doubles decide the 25→18
journey; approach quality and conversion decide 18→12; proximity and conversion
efficiency decide the climb below that. The Turn assigns a stage from your
rating-leveled scoring average, headlines the 3-4 metrics that matter AT YOUR
stage, and **graduates** a metric when you've sustained its target — it moves to a
quiet watchlist, the next lever is promoted, and the event is celebrated with its
SG receipt. A graduated metric that regresses comes back. Nothing shouts forever;
nothing is ignored forever. Your dashboard and your friend's dashboard should not
look the same, because your golf is not the same.

## Attention is the product (knows more than it shows)

The Turn tracks far more about your golf than it chooses to put in front of you.
Nothing is locked and nothing is hidden — tap into anything and the data is there —
but the product's job is to say: "yes, we're watching this; no, it doesn't deserve
your attention yet." A future-level checkpoint reads "tracked now — becomes a focus
at Convert," never "locked." The primary focus is chosen by DEVELOPMENTAL LEVERAGE —
whichever constraint the analysis believes buys the most strokes — not by whichever
metric is closest to failing. One thing is primary; everything else is one tap away.

## The honesty rules (why the numbers can be trusted)

1. The scorecard is truth; sensors are witnesses, not judges.
2. Every scoring-level comparison is leveled (course rating, never raw par) —
   including against published population data.
3. One scope per line; every rate carries its n; small samples are labeled, and
   "not enough data yet" is a valid, published answer.
4. Deterministic code computes; the AI coach narrates and prescribes but never does
   arithmetic. Population benchmarks are transcribed from cited sources, verbatim.
5. Plain words only. If a term needs a legend, it gets rewritten or explained where
   it stands. No dataset shorthand ever reaches a golfer.

## Article seeds (the Learn/blog backlog)

1. Was it good? — why every golf number needs a reference point
2. Strokes Gained for people who don't care about Strokes Gained
3. Green Zone: the stat GIR should have been (with the validation story)
4. Your par isn't the card's par — personal par and stroke budgets
5. The metric that matters now — stages, graduation, and why your app should know
   your level
6. Where doubles really come from (penalties, escalation chains, containment)
7. The coach that remembers — prescriptions, adherence, receipts
8. What your bracket actually does — reading published benchmarks honestly
