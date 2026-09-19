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

## Job queue
| # | Job | Spec | Track | Notes |
|---|-----|------|-------|-------|
| 1 | Approach Ladder | approach-ladder-spec.md ✅ | analytics | crew job #1 |
| 2 | Stages (KPI charter) | kpi-charter-spec.md ✅ + amend | analytics | adopt Stabilize/Control/Convert/Optimize/Refine names; home-screen construct |
| 3 | Shot Sequence Engine | TO SPEC | analytics | two-shot transitions; mistake amplification (improve/maintain/worsen after trouble) + opportunity conversion; lateral-vs-aggressive classifier = geometry heuristic calibrated on annotation ground truth; outputs transition tables per hole archetype (par 4: tee→approach→GZ; par 5: tee→advance→approach→GZ) |
| 4 | Multi-user Phase A | vnext2 brief §A | platform | path parametrization; cheap; can interleave anytime; Steve's fork = test case |
| 5 | AWS foundation | vnext2 brief | platform | S3 tenant contract, generate + annotation-form lambdas, auth choice |
| 6 | App shell v2 | mockup + IA goal | UI | the six screens (Home/Stage, Approach, Sequences, Round, Practice, Journey); frontend-design plugin governs the visual pass |
| 7 | Development / Practice Plans | needs Colby's real practice-plan example | UI | generalizes focus-card adherence |
| 8 | Diagnostician | TO SPEC, last | AI | iterative why-chain; agent CHOOSES deterministic queries, never computes (house rule); requires 1-3 as queryable primitives |

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
