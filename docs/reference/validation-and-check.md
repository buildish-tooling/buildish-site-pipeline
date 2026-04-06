---
weight: 17
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

# Validation and `site-pipeline check`

For maintainer-facing notes about shared evaluation ownership, stage-gating, and
the lower execution path reused by `check`, `build`, and `watch`, see
[code maintenance](/maintenance/code-maintenance/).

`site-pipeline check` should be the stable non-mutating command for validating a
workspace before staging.

It exists because the model now contains enough explicit routing, lifecycle,
localization, provider, and staged-metadata rules that "try to build and see what
happens" is too blunt for automation and day-to-day operator use.

## What `check` should do

`check` should load the same effective authored model that `build` depends on and
validate it without producing a stage tree.

Implementation-wise, `check` should reuse the same resolve, planning,
cross-reference, provider-merge, and validation code paths that `build` and the
per-cycle `watch` execution use.

The command boundary is that `check` stops before:

- stage-root preparation or cleanup
- file copying or mount materialization into the stage root
- aggregate metadata writes
- `manifest.json` creation
- watch-loop startup

In practice, that means validating at least:

- authored config shape and cross-reference integrity
- effective publication resolution, route uniqueness, and unique resolution of
  internal `route:` references
- redirect safety and internal-target validity
- page readability plus front matter parse and namespace rules
- localization policy shape, locale-prefix placement, and translation-link
  consistency
- provider snapshot shape, provider-to-authored merge assumptions, authored
  publication-selection references, authored release-line parent chains, and
  provider planning ceilings
- reserved front matter namespace rules such as authored `pipeline` collisions
- local input readiness that is necessary to say whether the current workspace is
  buildable

Where practical, `check` should aggregate independent failures into one report
instead of stopping at the first validation error.

## What `check` must not do

`check` is intentionally safe and non-mutating.

It must not:

- fetch from SCMs or release providers
- mutate caches or local input trees
- materialize missing inputs
- write or partially write staged output
- start a watch loop or renderer

## Exit behavior

The stable exit-code contract should be:

- `0`: validation completed and satisfied the active failure threshold
- `1`: validation completed but failed the active failure threshold
- `2`: invalid invocation, invalid option combination, or unsupported requested
  report schema version
- `3`: internal failure while attempting to evaluate the workspace

By default, the active failure threshold is `error`, so warnings do not fail the
command.

That keeps normal validation failure distinct from command failure while still
respecting common CLI expectations that `2` is reserved for usage or invocation
problems rather than ordinary domain failures.

## Warning policy

Warnings should remain advisory by default.

Recommended behavior is:

- warnings-only results still exit `0` by default
- `--fail-on warning` promotes warnings to a failing validation result with exit
  code `1`
- the diagnostic severities in the report do not change when strict mode is used;
  only the pass/fail threshold changes

## Recommended CLI syntax

The recommended stable command shape is:

- `site-pipeline check`
- `site-pipeline check --fail-on error`
- `site-pipeline check --fail-on warning`
- `site-pipeline check --report-format json --report-schema-version 1`
- `site-pipeline check --report-format json --report-schema-version 1 --report-output -`
- `site-pipeline check --report-format json --report-schema-version 1 --report-output .site-pipeline/check-report.json`

Recommended flag meanings are:

- `--report-format` accepts `text` or `json`; default is `text`
- `--report-schema-version` selects the requested `CheckReport.schemaVersion`
  and is required when `--report-format json` is selected
- `--report-output` selects the report destination; `-` means stdout and is the
  default. When set to a file path, that path is machine-local and follows the
  host operating system's native path rules rather than the pipeline's
  POSIX-only contract path rules.
- `--fail-on` accepts `error` or `warning`; default is `error`

That gives one clear contract for humans, CI, and wrapper scripts.

## Machine-readable report

For automation, `check` should support a machine-readable `CheckReport`.

Recommended rules:

- automation requests the desired report `schemaVersion` explicitly
- the emitted report includes the effective `schemaVersion`
- unsupported requested versions fail fast
- the report always includes a diagnostic array, even when it is empty
- the summary includes diagnostic counts, the active failure threshold, and an
  overall status so callers do not need to recompute them

The canonical typed shape lives in
[pipeline-model-schema-reference.md](pipeline-model-schema-reference.md).

## Relationship to planning and staging

The command split should stay sharp:

- `site-pipeline plan` answers **what inputs are needed** and whether they are
  present, missing, stale, or unresolved
- `site-pipeline check` answers **is the current workspace valid and ready to
  stage**
- `site-pipeline build` and `site-pipeline watch` perform staging

In other words, planning is about acquisition state, `check` is about validation
state, and `build`/`watch` are about stage production.

At the implementation level, though, `check`, `build`, and each `watch` cycle
should share one execution pipeline until the moment stage mutation begins.

## Relationship to staged diagnostics

`check` should reuse the same diagnostic entry shape used elsewhere in the model.

That keeps diagnostic codes, severity, and structured details consistent across:

- non-mutating validation reports
- planning diagnostics
- staged `data/diagnostics.json`

The shared typed shape is `PipelineDiagnosticEntry`.

`details` in that shape are supplemental structured context, not the sole
carrier of failure identity or location. The top-level diagnostic fields and
message should remain sufficient for an operator to understand what failed and
where. If a generated `details` object would exceed its hard ceiling, the
implementation must emit a bounded summary object, informally called
`ReducedDiagnosticDetailsSummary`, instead of the full details payload while
preserving a valid diagnostic entry. The recommended replacement fields are
`omitted`, `reason`, `actualBytes`, `limitBytes`, optional short `summary`, and
optional `fingerprint`.

When `build` or `watch` reporting is requested, those commands should reuse the
same collected diagnostics and summary counts in their machine-readable run
reports.

## Recommended use

The intended operator and automation flow is:

1. run `site-pipeline plan` when local-input acquisition is uncertain
2. materialize or refresh missing inputs outside the pipeline when needed
3. run `site-pipeline check`
4. run `site-pipeline build` or `site-pipeline watch`

That gives CI and local tooling a clean preflight command without blurring the
boundary between validation, materialization, and staging.

## Read next

- [api-contract.md](api-contract.md) for the stable CLI boundary
- [source resolution and materialization](/architecture/source-resolution-and-materialization/)
  for planning and local-input readiness
- [code maintenance](/maintenance/code-maintenance/) for maintainer-facing planning,
  evaluation, staging, and watch guardrails
- [flexible-component-publication.md](flexible-component-publication.md) for the
  validation rules `check` should enforce
- [pipeline-model-schema-reference.md](pipeline-model-schema-reference.md) for
  `CheckReport` and `PipelineDiagnosticEntry`