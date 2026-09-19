# Roadmap — the development-analytics era (agreed 2026-09-19)

*Sequencing decision for the post-benchmark work: the CGPT-assisted concept
(docs/development-analytics-concept.md, mockup at docs/assets/turn-concept.png)
mapped onto what exists, split into clean agent jobs. Companion specs:
approach-ladder-spec.md, kpi-charter-spec.md, vnext2-multi-tenant-vision.md.*

## The three convictions (Colby, 2026-09-19)
1. **Golfer Progression as a first-class construct** → the KPI charter, elevated:
   stage names Stabilize (25+) / Control (18-25) / Convert (10-18) / Optimize (5-10) /
   Refine (<5); home-screen presence (Stage → Priorities → Established skills → Next).
2. **Green Zone** → locked and validated; see approach-ladder-spec.md.
3. **Shot sequences over isolated strokes** → the genuinely new analytical layer.

## Sequencing principle
Split by what the work touches — NOT "multi-user first" vs "revisions first":
- **Track 1, analytics core, NOW, on the current pipeline:** derived-layer work is
  tenancy-independent, gate-protected, useful immediately (Colby + Steve's fork), and
  de-risks the product thesis before infrastructure spend. Everything exports clean
  JSON the future UI will consume.
- **Track 2, platform + UI, TOGETHER:** the six-screen app shell is a large front-end
  build — build it ONCE, on the multi-user AWS foundation (per-user JSON), never on
  the single-tenant static site. Current site stays live and absorbs only the minimal
  cards already spec'd (absorb-don't-add).
- Diagnostician + Practice Plans land last: they consume everything below.

## Sequencing correction (2026-09-19, Colby's catch)
**Engines never own presentation, and data contracts derive from DESIGNED screens.**
The charter/sequences are IA constructs — building their UI on the old site (or shaping
their JSON before the screens exist) is double work. So: UX Blueprint moves ahead of
the engines; engines ship math + JSON-per-contract + coach blocks + md only; app shell
v2 becomes assembly of an approved blueprint against contracts already carrying live
data.

## Job queue
| # | Job | Spec | Track | Notes |
|---|-----|------|-------|-------|
| 1 | Approach Ladder | approach-ladder-spec.md | analytics | ✅ SHIPPED (v1 + v1.1 merged + deployed 2026-09-19) |
| 2 | **UX Blueprint** | evolves FROM the work | UI | **INTERACTIVE — NOT a crew handoff.** Colby + Claude working sessions: brainstorm-first (superpowers:brainstorming), then a SERIES of clickable HTML mocks of the six screens fed by REAL exported data, iterated screen by screen (frontend-design plugin governs the visual pass). Deliverables when done: per-screen data contracts, component inventory, locked visual language → docs/ux-blueprint/. Gate: Colby approves each screen. |
| 3 | Stages engine (KPI charter) | kpi-charter-spec.md (amended: engine-only) | analytics | math + tier assignment + graduation state machine + JSON per blueprint contract + coach charter block + md. NO site presentation (at most a one-line stage chip on the current site). Stage names: Stabilize/Control/Convert/Optimize/Refine. |
| 4 | Shot Sequence Engine | TO SPEC | analytics | engine-only, same pattern; two-shot transitions; mistake amplification + opportunity conversion; lateral-vs-aggressive classifier = geometry heuristic calibrated on annotation ground truth; transition tables per hole archetype; screen-3 contract from the blueprint |
| 5 | Multi-user Phase A | vnext2 brief §A | platform | path parametrization; cheap; parallel-capable; Steve's fork = test case |
| 6 | AWS foundation | vnext2 brief | platform | S3 tenant contract, generate + annotation-form lambdas, auth choice |
| 7 | App shell v2 | the approved blueprint | UI | pure assembly: implement approved screens against contracts already fed by live engines |
| 8 | Development / Practice Plans | needs Colby's real practice-plan example | UI | generalizes focus-card adherence |
| 9 | Diagnostician | TO SPEC, last | AI | iterative why-chain; agent CHOOSES deterministic queries, never computes (house rule); requires 1/3/4 as queryable primitives |

## Branch discipline
All roadmap jobs build on **`dev-analytics`** (created 2026-09-19; builders' worktrees
stack on it). `main` stays production: daily syncs, update.sh, and deploys run from
main only, and new-round data commits keep landing there. The branch NEVER commits
data/processed regenerations — outputs are rebuilt at merge; rebase onto main
periodically to pick up new rounds. If the direction is hated, delete the branch;
main never felt it.

## Process rules for the crew
- architect → builder → test-runner per .claude/agents; superpowers plugin skills slot
  into process (writing-plans / executing-plans, test-driven-development,
  verification-before-completion, using-git-worktrees).
- Unattended/flight execution: prefer a CLOUD session (claude.ai/code) launched before
  boarding — survives a closed laptop; `/schedule` for recurring routines; local
  `/goal` + `caffeinate -dimsu` on the mac mini as fallback.
- Every job ends on its spec's verification gate; deploys and LLM-cost steps remain
  human-approved (settings.json).

## Concept-to-reality map (so nobody re-invents)
- CGPT §1 stages = kpi-charter-spec (rename only) · §4 Green Zone/ladder =
  approach-ladder-spec (ours is stricter: validated radius, computed payoff anchors) ·
  §7 evidence tiers = existing insight confidence + coverage badges · §8 IA = vnext2
  Phase B busy-ness goal, now with the six-screen answer · §9 thesis = vnext2
  positioning section.
- CGPT §3/§5 sequences and §6 diagnostician are the NEW work (jobs 3 and 8).
