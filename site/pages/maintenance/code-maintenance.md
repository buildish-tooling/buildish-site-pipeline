---
title: "Code maintenance and internal boundaries"
description: "This document is for maintainers of the Site Pipeline implementation."
weight: 19
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

The public reference and architecture docs define the public contract,
staged-output contract, schema shape, security model, and system shape. This
document records the durable internal boundaries and guardrails that future
refactors should preserve.

## Scope of this document

This document covers:

- internal package ownership and responsibility splits
- the shared execution path used by `plan`, `check`, `build`, and `watch`
- stage-publication and watch-mode invariants that protect renderer-visible
  integrity
- maintainer expectations for future refactors and test updates

It does not replace the stable public docs. When there is a conflict, the public
contract docs remain the source of truth for user-visible behavior.

## Internal package map

Keep the implementation split into a small number of boring, explicit layers.

### `models`

- owns external authored, provider, report, and staged-contract schema models
- owns local, deterministic validation of those external documents
- must not own coordinator state, worker state, or filesystem mutation logic

### `planning`

- loads workspace inputs through the model layer
- resolves effective authored configuration and provider authority boundaries
- derives selected version contexts, local-input inventory, readiness, and watch
  roots
- builds the immutable planning result and the build-plan candidate
- must not fetch from SCMs or providers, mutate caches, or write stage output

### `evaluation`

- consumes the immutable planning result
- runs shared non-mutating contextual validation for `check`, `build`, and each
  `watch` cycle
- produces deterministic diagnostics, summaries, and the stage-gating decision
- must not create stage directories, copy files, or publish output

### `staging`

- owns owned-unit execution, aggregate recomputation, publication preconditions,
  and finalized stage publication
- keeps worker writes inside private work areas
- keeps shared outputs, `manifest.json`, and visible-stage publication under the
  coordinator only

### CLI layer

- owns parsing, dispatch, text/json output rendering, and report-file writing
- translates internal outcomes into the public CLI contract from
  `api-contract.md`
- must not invent a second planning, evaluation, or staging path beside the
  shared lower execution layers

## Shared execution path

Keep one shared lower pipeline for the commands that evaluate a workspace.

1. load inputs and derive the immutable planning result
2. run shared evaluation and compute diagnostics plus stage gate
3. when staging is enabled, execute owned-unit staging and aggregate publication
4. emit the command-appropriate summary or report

The command split is:

- `plan`: planning/reporting only
- `check`: planning and evaluation only
- `build`: one full pass through planning, evaluation, and staging
- `watch`: repeated cycles that reuse the same planning, evaluation, and staging
  layers

Do not add a special-case validation path for `check` or a separate ad hoc
execution engine for `watch`. The lower layers must stay aligned so that a clean
`check` result means the same workspace is suitable for `build`, subject to the
same inputs and failure threshold.

## Stage-publication and watch invariants

The renderer-visible stage must stay coherent even during noisy or failing watch
cycles.

- the visible stage is always either the previous finalized state or the next
  finalized state, never a partially assembled hybrid
- workers never write directly into the visible stage
- the coordinator is the only writer of shared aggregates and `manifest.json`
- `manifest.json` is the commit point for a finalized stage update and must be
  written last
- failed watch cycles preserve the last-known-good stage
- when invalidation scope is uncertain, broaden the recomputation scope instead
  of guessing narrower
- watch-mode self-generated writes under pipeline-owned work roots, stage roots,
  and report outputs must not be treated as fresh authored input
- immediately before publication, revalidate path normalization, final-target
  non-symlink requirements, output ownership, and same-filesystem assumptions

Treat watch behavior as incremental recomputation, not incremental publication.
Optimizing recomputation is fine. Relaxing publication integrity is not.

## Watch operating modes

Watch correctness must hold in both notification-driven and polling-driven
environments.

- polling is a supported correctness mode, not a second-class fallback
- noisy, duplicate, delayed, or coalesced change bursts from bind-mounted,
  containerized, or macOS-hosted workspaces must converge to the same final
  result as a clean rebuild
- publication logic must not assume cross-filesystem atomic rename support; keep
  private work areas and finalized publication strategy aligned with the actual
  filesystem guarantees that exist at runtime

## Cross-cutting maintainer guardrails

Future refactors should continue to respect these rules:

- do not add hidden fetch, provider refresh, cache mutation, or renderer-specific
  behavior to planning, evaluation, or staging
- do not invent a second route, selection, or ownership algorithm in another
  layer; validate and stage the already resolved plan
- keep public reports and staged outputs free of machine-local implementation
  details beyond the documented contract
- keep report-file publication separate from stage publication
- keep security-sensitive defaults under local operator control rather than under
  repo-authored or provider-authored inputs

## Test-maintenance expectations

When changing these internals, update tests in the same area.

- planning changes need happy-path and failure-path coverage for resolution,
  readiness, and watch-root derivation
- evaluation changes need deterministic diagnostic and stage-gating coverage
- staging changes need ownership, collision, and publication-integrity coverage,
  including `manifest.json`-last behavior
- watch changes need burst, failure-retention, and self-write exclusion coverage
- when behavior is supposed to be shared across `check`, `build`, and `watch`,
  tests should make that reuse explicit

## Documentation structure and onboarding maintenance

Keep the documentation set split by reader need instead of mixing onboarding,
procedural guidance, and reference material into the same layer.

- `site/pages/getting-started/` is the onboarding layer for readers who first
  need to identify their site shape and the smallest model they need
- `site/pages/how-to/` is for task-oriented workflows such as building a tiny
  site, inspecting staged output, or generating HTTP server config
- `site/pages/architecture/` explains the system shape, rationale, and examples
- `docs/reference/` defines contracts, schemas, glossary material, and trust
  boundaries
- `site/pages/maintenance/` records durable maintainer guidance, while
  `docs/maintenance/todos.md` remains the backlog page for deferred follow-ups

When maintaining the onboarding docs, optimize for these outcomes:

- fast self-identification: "which kind of site am I?"
- a minimal mental model for the current audience
- explicit permission to ignore irrelevant complexity for now
- a clear path to the next size band when a site grows

The getting-started pages should keep a consistent shape:

- who this is for
- the smallest useful or smallest working model
- what can be ignored for now
- what to read next when the site grows

Use this consumability check when changing the onboarding docs. A reader should
be able to answer:

1. is this my size band?
2. what is the smallest model I need?
3. which advanced features can I safely ignore?
4. what should I read next if my site grows?

If those answers are hard to find, the model may still be sound, but the docs
set is not yet consumable enough.

## Read next

- [api contract](../../development/reference/api-contract/) for the public CLI boundary
- [../architecture/source-resolution-and-materialization.md](../../architecture/source-resolution-and-materialization/)
  for planning inputs and materialized-source boundaries
- [validation and check](../../development/reference/validation-and-check/) for shared validation
  semantics and `site-pipeline check`
- [../architecture/build-architecture.md](../../architecture/build-architecture/) for coordinator/worker execution
  structure and scaling shape
- [staged output contract](../../development/reference/staged-output-contract/) for the renderer-visible
  stage contract
- [security and trust model](../../development/reference/security-and-trust-model/) for path, URL, and
  trust-boundary requirements
- [user-facing-docs-strategy.md](../user-facing-docs-strategy/) for the planned
  user-facing documentation site shape
