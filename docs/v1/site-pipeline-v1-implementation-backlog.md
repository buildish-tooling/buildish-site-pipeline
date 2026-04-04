---
weight: 42
---

<!--
Copyright 2026 The Apache Software Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Site-pipeline v1 implementation backlog

This document is the high-level tracking backlog for implementing the full
site-pipeline feature set that is in scope for v1.

It is intentionally brief. The detailed implementation behavior, security rules,
and domain-specific test expectations remain defined by the implementation guides
and the normative v1 documents they reference.

## How to use this backlog

Use this file to track implementation progress at the workstream and milestone
level.

Do **not** use it as a replacement for the detailed guides.

For any work item below, the detailed guide checklist for that domain must also
be satisfied before the item is considered complete.

## Source documents for detailed execution

- `model-implementation-guide.md`
- `planning-and-input-resolution-implementation-guide.md`
- `evaluation-and-validation-implementation-guide.md`
- `stage-build-implementation-guide.md`
- `cli-api-implementation-guide.md`
- `watch-incremental-staging-plan.md`

## Tracking rules

- mark a phase complete only when its code, tests, and safety/security checks are
  complete
- do not mark a phase complete on happy-path behavior alone
- negative-path, edge-case, and security-sensitive tests are required work, not
  stretch work
- if a lower dependency phase is incomplete, do not treat a higher phase as done
  even if partial scaffolding exists
- when a guide and this backlog differ in detail, the guide wins

## Recommended implementation sequence

The implementation should progress in this order:

1. model layer
2. planning and input resolution
3. shared evaluation and contextual validation
4. staging/build engine
5. CLI and invocation/reporting integration
6. watch mode and retained-stage behavior
7. final hardening and whole-system verification

Some scaffolding can happen earlier, but merges should respect those dependency
boundaries.

## Phase 1: model layer

- [x] implement the external model package and document loaders
- [x] implement shared scalar and validation helpers
- [x] implement schema-version dispatch and duplicate-key rejection
- [x] implement output-facing report/staged models needed by later phases
- [x] add thorough positive, negative, boundary, and security-sensitive tests

Primary reference:

- `model-implementation-guide.md`

Merge gate:

- all externally loaded documents and emitted report/staged models used in v1 are
  typed, validated, and covered by unhappy-path tests

## Phase 2: planning and input resolution

- [x] implement effective authored configuration resolution
- [x] implement provider snapshot indexing and authority boundaries
- [x] implement version-context selection
- [x] implement local-input inventory and readiness classification
- [x] implement watch-eligibility and watch-root derivation
- [x] implement `ResolvedMaterializationReport`
- [x] implement `PlanningEvaluation` and optional `EffectiveBuildPlan` candidate
- [x] add deterministic and security-sensitive tests for planning behavior

Primary reference:

- `planning-and-input-resolution-implementation-guide.md`

Merge gate:

- planning is non-mutating, deterministic, path-safe, and covers the full input
  universe actually consumed by `build` and `watch`

## Phase 3: shared evaluation and contextual validation

- [x] implement the shared evaluation package used by `check`, `build`, and
      `watch`
- [x] implement the central diagnostic collector and code registry
- [x] implement contextual reference, route, redirect, localization, provider,
      readiness, and page-scan validation modules
- [x] implement summary construction and explicit stage-gating decisions
- [x] add deterministic, non-happy-path, and security-sensitive evaluation tests

Primary reference:

- `evaluation-and-validation-implementation-guide.md`

Merge gate:

- `check`-equivalent evaluation can run without stage mutation and produces
  trustworthy diagnostics, summaries, and stage-gating decisions

## Phase 4: staging/build engine

- [ ] implement the internal staging runtime types and work-area model
- [ ] implement coordinator and worker boundaries
- [ ] implement owned-unit staging for site pages, site assets, vendor assets,
      and components
- [ ] implement aggregate assembly, ownership validation, and manifest building
- [ ] implement private-stage assembly and safe visible publication
- [ ] add correctness, ownership, collision, publication, and failure-path tests

Primary reference:

- `stage-build-implementation-guide.md`

Merge gate:

- one-off `build` can produce a trustworthy finalized stage with manifest-last
  publication semantics and no unresolved integrity gaps

## Phase 5: CLI and invocation/reporting integration

- [x] implement the stable `plan`, `check`, `build`, and `watch` command surface
- [x] implement immutable invocation objects and parser validation
- [x] implement exit-code mapping and command dispatch
- [x] implement safe text/JSON report emission and report-file writing
- [x] integrate command handlers with the shared lower-layer execution path
- [x] add parser, output, exit-code, and report-write safety tests

Primary reference:

- `cli-api-implementation-guide.md`

Merge gate:

- the public CLI contract is stable for v1, report output is safe, and command
  outcomes match the documented semantics exactly

## Phase 6: watch mode and retained-stage behavior

- [x] implement the watch coordinator and explicit cycle state model
- [x] implement dirty-set handling and watch-root refresh behavior
- [x] implement per-cycle reuse of planning, evaluation, and staging
- [x] implement retained last-known-good behavior for ordinary cycle failure
- [x] implement exit-required behavior for integrity ambiguity
- [x] implement repeated watch-report rewriting without self-trigger loops
- [ ] add state-machine, invalidation, filesystem-transition, and safety tests

Primary reference:

- `watch-incremental-staging-plan.md`

Merge gate:

- watch mode preserves correctness and stage integrity under both normal rebuilds
  and failure conditions; it must not lie about stage usability

## Phase 7: final hardening and whole-system verification

- [ ] verify all v1 in-scope functionality is implemented across all phases
- [ ] verify all documented security ceilings and safe defaults are enforced
- [ ] verify all report contracts and staged-output contracts are honored
- [ ] verify non-happy-path coverage across planning, validation, staging, CLI,
      and watch behavior
- [ ] verify whole-system behavior is deterministic enough for stable tests and
      safe operator use
- [ ] resolve any remaining ambiguity between guides, code, and tests before v1
      completion

Primary references:

- all implementation guides
- all v1 normative docs those guides depend on

Merge gate:

- the implementation is feature-complete for v1 scope and there are no known open
  correctness, security, safety, or contract-alignment blockers

## Cross-cutting done criteria for the whole project

Do not consider v1 complete until all of the following are true:

- [ ] all v1 in-scope behavior has an implementation
- [ ] all implementation-guide domain checklists are satisfied
- [ ] all relevant unhappy-path and security-sensitive tests exist and pass
- [ ] no phase relies on hidden fetches, hidden mutation, or undocumented side
      paths
- [ ] no public report or staged output leaks machine-local implementation detail
      beyond the documented contract
- [ ] watch, build, and check all reuse the intended shared lower execution path
- [ ] stage publication remains integrity-first, with `manifest.json` as commit
      point

## Out-of-scope guardrail

This backlog is only for work that is in scope for v1 as defined by the current
v1 documentation set.

Do not use it to smuggle in:

- post-v1 feature expansion,
- renderer-owned features outside current scope,
- new public APIs beyond the `site-pipeline` executable, or
- relaxed security/safety behavior in exchange for convenience.

## Bottom line

This file should stay the high-level tracker.

The implementation guides remain the detailed execution manuals.