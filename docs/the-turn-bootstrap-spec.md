# the_turn — bootstrap & migration spec

*Approved 2026-09-19. The product outgrew "Colby's golf helper": new repo `the_turn`,
multi-user from day one, AWS-native. This job stands the new house up and moves the
crown jewels in — a MIGRATION, NOT A REWRITE. The engines (sg_core, sha-gated ingest,
phantom detection, ladder, benchmarks, insights, coach, 116+ tests, the parity gate)
are battle-tested; port them, don't re-derive them. Re-fighting won wars is the
failure mode this spec exists to prevent.*

## Endgame roles
- **the_turn** — the product. All future feature work (roadmap jobs 3, 4, 7, 8, 9).
- **garmin-golf** — Colby's production daily tool UNTIL the_turn reaches output
  parity and cuts over; then it retires into the Garmin edge connector + his personal
  data archive. **Bright line: once the_turn is bootstrapped, garmin-golf is
  feature-frozen (critical fixes only).** One math, one home — engine copies must
  never drift.

## Target layout
```
the_turn/
├── engines/              # the ported pipeline
│   ├── turn/             # python package (garmin-golf src/, module names preserved)
│   ├── sql/schema/       # DDL, filename-ordered (unchanged)
│   ├── tests/            # ported suite + fixtures (fixture round 999000111)
│   └── tools/parity.py
├── connectors/
│   ├── garmin_edge/      # pull agent: runs at the user's edge, uploads raw to the
│   │                     # tenant inbox (extracted from pull.py/garmin_client.py;
│   │                     # credentials NEVER server-side)
│   └── birdies18/        # placeholder — Steve's path becomes first-class here
├── shell/                # app shell v2 (job 7; built from docs/ux-blueprint)
├── infra/                # IaC (CDK or Terraform — architect's call): tenant bucket,
│                         # generate + annotation-form lambdas, CloudFront, auth
├── config/               # SHARED analytics config only (sg_baseline,
│                         # benchmarks_broadie, ladder bins, stage definitions)
├── docs/                 # the migrated brain (see below) + new ADR #1
└── .claude/              # crew + permissions, migrated and path-adapted
```

## The tenancy contract (v0, local-first)
A **tenant root** is a directory shaped `{raw/, annotations/, config/, processed/}` —
identical to garmin-golf's `data/` + per-tenant config. Every engine path constant
becomes derived from the tenant root (this IS the old Phase A work, done once, here).
Per-tenant config = golfer_profile.md, clubs.json, courses, publish/coach settings.
Shared config (the math) stays in the repo. The S3 mapping is the same shape at
`s3://<bucket>/users/<id>/…` — documented now, wired in phase 3. **No tenant data is
ever committed to the_turn** — tenant roots live outside the repo (dev fixtures
excepted).

## Migration map
- **Ports verbatim** (import/path changes only): every engine module in `src/`,
  `sql/schema/`, `tests/` + fixtures, `tools/parity.py`, shared config JSONs.
- **Transforms:** path constants → tenant-root resolution (one context object, not
  scattered env vars); `update.py` → a per-tenant run entrypoint (local mode now, a
  thin lambda handler wrapper later); `site.py` keeps producing the single-file site
  per tenant — it remains the render layer until the shell (job 7) replaces it, and
  it is the parity instrument.
- **Stays in garmin-golf:** all of `data/` (Colby's raw/annotations/processed),
  `update.sh` + bot flow (edge machinery — later absorbed by connectors/garmin_edge),
  the colbyward.io publish flow.
- **Docs migrate:** philosophy.md, decisions.md (all ADRs, + new ADR: this bootstrap),
  roadmap.md (rewritten for the new home), all specs, ux-blueprint/ (decisions log +
  prototype.html). architecture.md is REWRITTEN by the architect for the new layout.
- **Crew migrates:** .claude/agents (references updated to new paths) +
  settings.json permissions (same allow/ask/deny philosophy, new paths).

## Phases & gates (each gated before the next)
1. **Port.** Layout up; engines/tests/config moved verbatim; `pytest` green (116+),
   `ruff` clean — in the new repo, before any refactor.
2. **Tenant-root parametrization + THE PARITY GATE.** Point a read-only tenant root
   at a garmin-golf checkout's data. The ported pipeline's `processed/` outputs and
   generated site must match garmin-golf's current outputs — byte-identical, or every
   diff explained (e.g., embedded generation dates). tools/parity clean. This gate is
   the migration's entire proof: same inputs, same math, same outputs, new house.
3. **Infra skeleton.** IaC scaffold: versioned tenant bucket, lambda stubs (generate,
   annotation-form), CI running the full gate on push. No production deploy required
   to pass — the skeleton exists, applies cleanly, and is documented.

## Rules for the crew
- Architect plans first (refine this map; pick IaC tool; design the tenant-root
  context object). Builders port in worktrees; test-runner issues the verdicts.
- NEVER "improve" an engine during the port — behavior-preserving moves only. Every
  improvement idea goes in a `docs/port-notes.md` list for later, not into the diff.
- No credentials, no tenant data, no publish targets in the repo. Private repo.
- Commit attribution per house convention.

## After bootstrap
- Roadmap jobs 3 (stages engine), 4 (sequences), 7 (shell), 8, 9 run in the_turn.
- garmin-golf: bright line applies; Colby's daily flow unchanged until cutover.
- Cutover (its own later decision): Colby's raw uploads target the tenant inbox;
  garmin-golf archived read-only.
