---
weight: 18
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

# Evaluation and validation implementation guide

This document tells implementers how to build the shared non-mutating evaluation
layer used by `check`, `build`, and each `watch` cycle before stage mutation
begins.

It is intentionally prescriptive. The goal is that a junior engineer can follow
it directly without inventing local rules for contextual validation, diagnostic
collection, route/redirect checks, provider-context validation, or stage gating.

This guide complements:

- `validation-and-check.md` for the public semantics of `site-pipeline check`
- `planning-and-input-resolution-implementation-guide.md` for the resolved input
  and immutable build-plan layer consumed here
- `build-architecture.md` for the shared `check`/`build`/`watch` execution path
- `stage-build-implementation-guide.md` for the staging layer that runs only after
  successful evaluation
- `watch-incremental-staging-plan.md` for watch-cycle failure handling and
  retained-stage semantics
- `pipeline-model-schema-reference.md` for `CheckReport`, `CheckSummary`,
  `StageRunReport`, `StageRunSummary`, and `PipelineDiagnosticEntry`
- `security-and-trust-model.md` for path, trust, URL, and limit rules
- `flexible-component-publication.md` for publication, routing, localization,
  provider, and validation expectations
- `provider-to-staged-metadata-mapping.md` for provider-related staged-metadata
  expectations

## Scope

This guide is about contextual validation and shared evaluation only.

It covers:

- the shared resolve-and-validate execution path below the CLI,
- contextual validation beyond raw model parsing,
- diagnostic construction and aggregation,
- route, redirect, localization, provider, and input-readiness validation,
- stage-gating decisions,
- `CheckSummary`/run-summary construction inputs, and
- evaluation-focused tests.

It does **not** cover:

- external document parsing,
- CLI parsing or exit-code mapping,
- stage mutation or publication,
- watch-loop filesystem watching,
- renderer behavior.

## Fixed decisions

Implementers should treat the following as already decided:

1. `check`, `build`, and each `watch` cycle share one execution path until stage
   mutation begins.
2. Raw model-layer validation is not enough. Contextual validation must handle
   route uniqueness, rooted path checks, provider-context matching, and local
   input readiness.
3. `check` is non-mutating and must stop before any stage-root preparation,
   aggregate writes, or `manifest.json` creation.
4. Independent failures should be aggregated where practical instead of stopping
   at the first error.
5. `PipelineDiagnosticEntry` is the one shared diagnostic shape for planning,
   checking, and staging.
6. Oversized diagnostic `details` payloads must be reduced to
   `ReducedDiagnosticDetailsSummary`, not dropped or emitted as malformed JSON.
7. Domain failures that are expected outcomes of evaluation should become typed
   diagnostics and command results, not uncaught exceptions.
8. Evaluation must not fetch from SCMs or providers, mutate caches, or write
   staged output.
9. The evaluation layer must not invent a second route or selection algorithm.
   It validates the resolved plan produced by the planning layer.
10. A stage-capable command may proceed to staging only when evaluation has
    produced a trustworthy stage gate and an `EffectiveBuildPlan` to hand to
    staging.

## Required package layout

Create one dedicated internal package for shared evaluation.

Required layout:

- `apache_buildish_site_pipeline/evaluation/__init__.py`
- `apache_buildish_site_pipeline/evaluation/types.py`
- `apache_buildish_site_pipeline/evaluation/diagnostic_codes.py`
- `apache_buildish_site_pipeline/evaluation/collector.py`
- `apache_buildish_site_pipeline/evaluation/execution.py`
- `apache_buildish_site_pipeline/evaluation/reference_index.py`
- `apache_buildish_site_pipeline/evaluation/publication.py`
- `apache_buildish_site_pipeline/evaluation/routes.py`
- `apache_buildish_site_pipeline/evaluation/localization.py`
- `apache_buildish_site_pipeline/evaluation/providers.py`
- `apache_buildish_site_pipeline/evaluation/inputs.py`
- `apache_buildish_site_pipeline/evaluation/page_scan.py`
- `apache_buildish_site_pipeline/evaluation/limits.py`
- `apache_buildish_site_pipeline/evaluation/summary.py`

Keep this package separate from:

- `models.validation`, which owns pure reusable model-layer validators,
- `planning`, which owns effective resolution and local-input inventory, and
- `staging`, which owns filesystem mutation and publication.

## Responsibility split

Use this split consistently.

### `models.validation`

- scalar syntax validation
- field-local URL/path/reference grammar checks
- pure helper validation that does not need live filesystem or cross-document
  context

### `planning`

- resolve authored policy
- index provider snapshot records
- derive selected version contexts
- classify local-input readiness
- build the immutable plan

### `evaluation`

- build contextual indexes
- validate route ownership and route graph integrity
- validate redirects and internal references against known targets
- validate localization and translation relationships
- validate provider-record/context matching
- validate input readiness as a stage-gating condition
- scan selected authored page trees for reserved-namespace violations
- collect diagnostics and build summaries

### `staging`

- run only after evaluation passes enough for staging

## Main execution contract

The evaluation layer should expose one primary entry point in `execution.py`.

Recommended contract:

- input: one immutable evaluation request plus `PlanningEvaluation`
- output: one immutable `EvaluationResult`

`EvaluationResult` should contain at least:

- the evaluation mode (`check`, `build`, or `watch`),
- the evaluated planning result,
- the collected diagnostics,
- diagnostic counts and overall status,
- whether staging may proceed,
- the optional `EffectiveBuildPlan` that staging may consume when the gate
  passes,
- any derived contextual indexes useful to staging,
- any hard-failure flag indicating an internal or integrity-level problem rather
  than ordinary domain validation failure.

## Required internal types

Define internal dataclass-based runtime types in `types.py`.

### 1. Evaluation request/result types

Required types:

- `EvaluationMode`
- `EvaluationRequest`
- `EvaluationResult`
- `EvaluationStatus`
- `DiagnosticCounts`

### 2. Context index types

Required types:

- `ReferenceIndex`
- `PublicationIndex`
- `PublishedTarget`
- `RouteCandidate`
- `RedirectCandidate`
- `TranslationIndex`
- `ProviderMatchIndex`

These indexes should contain the normalized contextual views needed to validate
the resolved plan deterministically.

### 3. Diagnostic support types

Required types:

- `DiagnosticSeed`
- `DiagnosticLocation`
- `ReducedDiagnosticDetailsSummaryRuntime`
- `LimitObservation`

### 4. Stage-gating types

Required types:

- `StageGateDecision`
- `BlockingCondition`
- `EvaluationArtifacts`

`StageGateDecision` should explain why staging is allowed or blocked without
forcing callers to rediscover that logic from raw diagnostics.

## Diagnostic collection rules

Implement one central collector in `collector.py`.

### Non-negotiable collector behavior

1. The collector builds only valid `PipelineDiagnosticEntry` values.
2. Diagnostic codes come from one central registry in `diagnostic_codes.py`.
3. The collector reduces oversized `details` payloads to
   `ReducedDiagnosticDetailsSummary` according to the documented rule.
4. The collector keeps top-level fields (`severity`, `code`, `message`, optional
   `componentSlug`, `artifactKey`, `targetId`) operator-sufficient even when
   `details` are reduced.
5. Domain validation does not raise exceptions after the collector already knows
   how to represent the problem.

### Deterministic ordering rule

Diagnostics in reports should be deterministic enough for stable tests.

Use one explicit sort key before final report emission, for example by:

1. severity order,
2. code,
3. component slug,
4. artifact key,
5. target ID,
6. message.

Do not rely on filesystem iteration order or set iteration order.

### Severity policy

Use explicit rules.

- problems that prevent a trustworthy stage or a valid `check` pass are `error`
- advisory but non-blocking issues are `warning`
- informative status notes are `info`

Do not change diagnostic severities because `check --fail-on warning` was
requested. That option changes only pass/fail threshold behavior.

## Shared evaluation pipeline

Implement the evaluation pipeline in ordered phases.

### Phase 0: obtain the resolved plan

The evaluation layer consumes the immutable `PlanningEvaluation` result produced
by planning.

That planning result may already carry an optional `EffectiveBuildPlan`
candidate. Evaluation validates the broader contextual picture and decides
whether that plan may actually be handed to staging.

It must not:

- reload authored or provider documents through ad hoc side paths,
- rebuild a separate effective-config view,
- recalculate a different version-context selection algorithm.

### Phase 1: build contextual indexes

In `reference_index.py`, `publication.py`, and `providers.py`, build indexes for:

- known components, artifacts, release lines, releases, and named refs,
- resolved origins and public-path candidates,
- redirect candidates and internal target references,
- provider records matched to known version contexts,
- translation-set and locale relationships.

### Phase 2: run validation modules

Run each module independently where practical and add diagnostics to the shared
collector.

### Phase 3: compute summary and stage gate

After all validation modules run:

- compute counts,
- compute `RunStatus`,
- compute check-style pass/fail threshold results when needed,
- decide whether staging may proceed.

## Validation module requirements

### 1. Reference and graph validation

Implement contextual reference checks in `reference_index.py`.

Validate at least:

- unknown or duplicate artifact references within a component,
- broken release-line parent chains,
- cycles in release-line ancestry,
- unknown named-ref keys referenced by policy,
- unknown exact versions referenced by selection or authored release behavior,
- compatibility references that point to unknown subjects or targets.

Reference grammar parsing belongs in the model layer. Contextual existence checks
belong here.

### 2. Publication and route validation

Implement publication and route checks in `publication.py` and `routes.py`.

Validate at least:

- every publishable target resolves to one `(origin, path)` pair,
- origins are defined,
- public paths are absolute and canonical per the contract,
- `(origin, path)` collisions are rejected,
- case-only collisions are rejected,
- canonical routes are unique,
- alias routes do not conflict with canonical or redirect routes,
- overlapping component or mount ownership within one origin is rejected,
- site-owned versus component-owned collisions are rejected,
- route labels such as `latest` or `stable` resolve deterministically.

Do not let route uniqueness depend on the eventual staging filesystem layout.

### 3. Redirect validation

Redirect validation belongs with route validation.

Validate at least:

- internal redirect targets resolve to known routes or typed targets,
- external redirect targets use allowed URL schemes only,
- redirect status codes are from the supported set,
- redirect loops are rejected,
- redirects to unknown internal targets are rejected,
- withdrawn/tombstoned releases using `withdrawalBehavior: redirect` have a
  redirect target.

### 4. Localization and translation validation

Implement localization checks in `localization.py`.

Validate at least:

- duplicate locales within one translation set,
- conflicting translation linkage for one page,
- incompatible locale route mode/origin configuration,
- translated sibling routes that do not resolve consistently,
- default-locale assumptions that conflict with authored policy.

### 5. Provider contextual validation

Implement provider-related checks in `providers.py`.

Validate at least:

- provider records map to known component/artifact identities,
- provider-backed pages and version contexts map to exactly one normalized record
  when a mapping is expected,
- multiple normalized records do not compete for one staged page context,
- provider data does not redefine authored route ownership,
- provider-specific passthrough fields are not copied into public staged outputs,
- internal-only provider endpoints do not leak into public aggregates.

### 6. Input-readiness validation

Implement input-readiness gating in `inputs.py`.

The planning layer produces `present`/`missing`/`stale`/`unresolved` states.
Evaluation decides how they affect stage readiness.

Required first-wave policy:

- required inputs with `missing`, `stale`, or `unresolved` block staging,
- those states become diagnostics rather than a second planning report,
- `check` reports them as validation failures,
- `build` and `watch` stop before stage mutation when they are blocking.

### 7. Page scan and reserved-namespace validation

Implement read-only page scanning in `page_scan.py`.

Validate at least:

- authored pages do not define the reserved top-level `pipeline` namespace,
- selected page roots do not contain malformed front matter that would make the
  eventual staged page contract ambiguous,
- path-bearing page-level references stay within declared source roots after
  normalization and symlink resolution.

This scan is read-only. It must not rewrite source pages.

### 8. Limits and safety-default validation

Implement scale and limit checks in `limits.py`.

Enforce at least:

- hard non-overridable security ceilings from the security doc,
- safe operational defaults for route count, redirect count, content-index size,
  watched-root breadth, staged version-context count, and provider snapshot size,
- explicit diagnostics reporting measured and allowed values when limits are hit.

Hard ceilings must fail fast. Safe-default breaches should also fail unless a
local operator policy intentionally raised the limit.

## Stage-gating behavior

Evaluation is the last non-mutating gate before staging.

### Required stage-gating rule

Staging may proceed only when:

- no blocking `error` diagnostics remain,
- no required input is `missing`, `stale`, or `unresolved`,
- route ownership is unambiguous,
- redirect and publication targets are valid,
- no hard security ceiling was exceeded,
- an `EffectiveBuildPlan` is available to hand to staging,
- the build plan still describes a trustworthy staging attempt.

### Command-specific effect

- `check` stops here and emits `CheckReport`
- `build` calls the staging layer only if the gate passes
- `watch` calls the staging layer per cycle only if the gate passes; otherwise it
  reports the failed cycle and lets watch-state rules decide whether a retained
  stage remains usable

## Summary construction

Implement summary construction in `summary.py`.

### `CheckSummary`

Build `CheckSummary` from collected diagnostics and the active failure threshold.

Preserve the normative combinations from the schema reference:

- `clean` + passed
- `warnings` + passed under `failOnSeverity: error`
- `warnings` + failed under `failOnSeverity: warning`
- `errors` + failed

### Run-summary inputs

For `build` and `watch`, evaluation should provide the staging layer and CLI with
the summary inputs needed later, including:

- diagnostic counts,
- overall status,
- whether staging was allowed,
- whether the failure was an ordinary domain failure or an internal/integrity
  failure.

Do not let later layers recompute those facts from raw diagnostics ad hoc.

## Security-critical evaluation rules

### No mutation rule

Evaluation must not:

- fetch from SCMs or providers,
- mutate caches,
- materialize missing inputs,
- write stage-root content,
- write aggregate files,
- create `manifest.json`.

### Rooted path and symlink rule

When contextual validation needs filesystem trust decisions, it must:

1. normalize the path,
2. resolve symlinks before trust decisions,
3. reject escapes from declared roots,
4. reject ambiguous rooted identity.

### Operator policy stays local

Limit overrides, development-only scheme relaxations, watch breadth knobs, and
similar execution policy must stay local.

They must not come from:

- repo-authored metadata,
- provider-authored snapshot data,
- staged source content.

### Public outputs stay free of machine-local details

Evaluation-generated diagnostics and summaries that later become public reports or
staged metadata should avoid leaking:

- internal cache layout,
- private work-area paths,
- internal-only provider endpoints,
- temp-file names,
- unrelated absolute local paths.

## Recommended implementation order

Implementers should follow this order.

### Phase 0: diagnostics and summary core

1. Create the `evaluation` package and runtime types.
2. Implement the diagnostic code registry and collector.
3. Implement summary construction for `CheckSummary` semantics.
4. Add tests for deterministic ordering and detail reduction.

### Phase 1: contextual indexes and route validation

1. Implement `reference_index.py`, `publication.py`, and `routes.py`.
2. Add tests for route collisions, alias/canonical conflicts, and redirect loops.
3. Prove that route validation works from the resolved plan rather than a second
   ad hoc resolution path.

### Phase 2: provider, localization, and readiness validation

1. Implement `providers.py`, `localization.py`, and `inputs.py`.
2. Add tests for provider-context mismatches and translation inconsistencies.
3. Add tests for `missing`/`stale`/`unresolved` readiness becoming blocking
   diagnostics.

### Phase 3: page scanning, limits, and execution orchestration

1. Implement `page_scan.py` and `limits.py`.
2. Implement the main evaluation entry point in `execution.py`.
3. Add tests proving `check` stops before stage mutation.
4. Add tests proving stage-capable commands proceed only when evaluation passes.

## Required tests

Recommended test layout:

- `tests/evaluation/test_collector.py`
- `tests/evaluation/test_summary.py`
- `tests/evaluation/test_reference_index.py`
- `tests/evaluation/test_routes.py`
- `tests/evaluation/test_publication.py`
- `tests/evaluation/test_localization.py`
- `tests/evaluation/test_providers.py`
- `tests/evaluation/test_inputs.py`
- `tests/evaluation/test_page_scan.py`
- `tests/evaluation/test_limits.py`
- `tests/evaluation/test_execution.py`

### Collector tests

Test at least:

- valid `PipelineDiagnosticEntry` construction,
- deterministic sort order,
- details reduction to `ReducedDiagnosticDetailsSummary`,
- preservation of top-level operator-essential fields,
- no malformed JSON-producing states.

### Route and redirect tests

Test at least:

- `(origin, path)` collision rejection,
- case-only collision rejection,
- canonical-route uniqueness,
- alias/redirect conflicts,
- internal redirect resolution,
- redirect-loop rejection,
- unsupported external redirect-scheme rejection.

### Provider and readiness tests

Test at least:

- provider record mapping to unknown component/artifact,
- multiple provider records competing for one version context,
- authored policy winning over provider publishability,
- `missing`, `stale`, and `unresolved` inputs blocking staging,
- no hidden materialization behavior during evaluation.

### Page-scan and security tests

Test at least:

- authored `pipeline` namespace rejection,
- malformed source front matter behavior,
- rooted path checks for page-scanned inputs,
- no machine-local private paths leaking into public diagnostics by default.

### Execution tests

Test at least:

- `check` stops before stage mutation,
- stage-capable commands do not proceed when the gate fails,
- clean pass produces a stage-allowing result,
- warnings-only result remains stage-allowing when no blocking error exists,
- internal/integrity failures are distinguished from normal domain failures.

## Review checklist before merging evaluation code

### Structure

- [x] one dedicated `evaluation` package exists
- [x] model-layer validation and contextual validation are separated clearly
- [x] the evaluation layer consumes the resolved plan rather than rebuilding its
      own planning logic
- [x] one central diagnostic collector exists

### Correctness

- [x] route uniqueness is validated deterministically
- [x] redirect targets are validated against known targets and allowed schemes
- [x] provider-context matching is validated
- [x] readiness states become diagnostics and stage-gating decisions
- [x] `check` summary combinations match the schema contract
- [x] stage gating is explicit rather than inferred ad hoc in later layers

### Security

- [x] evaluation performs no hidden mutation or fetches
- [ ] rooted path and symlink checks are applied before trust decisions
- [x] oversized diagnostic details are reduced safely
- [x] operator policy is not repo/provider driven
- [x] machine-local details are kept out of public outputs by default

## Bottom line

If implementers follow this guide, the result should be:

- one shared non-mutating evaluation layer,
- one clear split between planning, contextual validation, and staging,
- one deterministic route/provider/readiness validation path,
- one central diagnostic collector that stays valid under stress,
- and one explicit stage gate that `check`, `build`, and `watch` can all trust.