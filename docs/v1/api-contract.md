---
weight: 12
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

# Site Pipeline API and contract boundaries

This document defines the public contract boundaries for the Site Pipeline.

The intended principle is:

> The `site-pipeline` executable is the only supported invocation API for stable
> planning, validation, and staging operations, specifically `plan`, `check`,
> `build`, and `watch`; the staged tree and aggregate metadata are the supported
> output API for downstream renderers and deployment adapters.

## Why this boundary exists

The architecture depends on a clean separation of responsibilities:

- the pipeline owns staging,
- the renderer owns rendering, and
- the consumer owns renderer-specific local development orchestration.

That split keeps the core pipeline portable, container-friendly, and independent
of Hugo, Node-based renderers, themes, dev-server behavior, or publishing logic.

## Stable invocation API

The stable control-plane API is the `site-pipeline` CLI.

The long-term stable commands are:

- `site-pipeline plan`
- `site-pipeline check`
- `site-pipeline build`
- `site-pipeline watch`

Those commands are the supported way to:

- discover required local inputs before staging,
- validate the current workspace and local inputs before staging,
- trigger one-off staging,
- keep staged outputs fresh during local editing,
- run the pipeline in CI,
- invoke the pipeline from container images, and
- integrate the pipeline into editor tasks or consumer wrapper scripts.

The exact CLI surface can evolve, but changes to `plan`, `check`, `build`, and
`watch` should be treated as compatibility-sensitive API changes rather than
ordinary refactoring.

## Stable validation command

`site-pipeline check` is the stable non-mutating validation command.

It should:

- load effective authored configuration and available local inputs
- run the same core structural, routing, publication, and metadata validation
  rules that `build` depends on
- aggregate independent diagnostics where practical instead of stopping at the
  first error
- support machine-readable output for automation

`check` should reuse the same resolve-and-validate execution path that `build`
and `watch` depend on, but stop before any stage-root mutation, file copying,
aggregate output writes, or watch-loop startup.

It must not:

- fetch from SCMs or providers
- mutate caches or local input trees
- write or partially write a staged output tree

By default, validation returns exit code `0` when no error diagnostics are
present, even if warning diagnostics are present.

The stable exit-code contract should be:

- `0`: validation completed and satisfied the active failure threshold
- `1`: validation completed but failed the active failure threshold
- `2`: invalid invocation, invalid option combination, or unsupported requested
  report schema version
- `3`: internal failure while attempting to evaluate the workspace

`site-pipeline check --fail-on warning` is a recommended strict mode for callers
that want warning diagnostics to produce exit code `1` without changing the
machine-readable diagnostic severities themselves.

The public contract should stay within these low application-owned exit codes and
avoid depending on shell- or signal-reserved ranges.

## Recommended `check` CLI syntax

The stable CLI option names for `check` should use kebab-case because they are
command-line surface, not input/output model fields.

Recommended forms are:

- `site-pipeline check`
- `site-pipeline check --fail-on error`
- `site-pipeline check --fail-on warning`
- `site-pipeline check --report-format json --report-schema-version 1`
- `site-pipeline check --report-format json --report-schema-version 1 --report-output -`
- `site-pipeline check --report-format json --report-schema-version 1 --report-output .site-pipeline/check-report.json`

Recommended flag meanings are:

- `--report-format` accepts `text` or `json`; default is `text`
- `--report-schema-version` selects the machine-readable report schema version
  and is required when `--report-format json` is selected
- `--report-output` selects the report destination; `-` means stdout and is the
  default
- `--fail-on` accepts `error` or `warning`; default is `error`

## Shared report flags

The stable machine-readable report flag family should be shared across all
report-capable commands:

- `--report-format`
- `--report-schema-version`
- `--report-output`

When `--report-format json` is selected, `--report-schema-version` is required.
Omitting it is an invalid invocation and should return exit code `2`.

That shared flag family should apply to:

- `site-pipeline plan`
- `site-pipeline check`
- `site-pipeline build`
- `site-pipeline watch`

Command-specific flags such as `--fail-on` may extend that shared base.

## Stable planning command

`site-pipeline plan` is the stable non-mutating planning command.

It should:

- emit machine-readable planning data such as a resolved materialization report,
- help consumers discover missing or stale local inputs before staging, and
- do not fetch from SCMs or mutate caches themselves.

For automation, callers should be able to request a specific planning-report
schema version explicitly.

Recommended behavior is:

- callers select an explicit planning target such as `build` or `watch`
- callers may request a report schema version explicitly
- the output includes the effective `schemaVersion`
- unsupported requested versions fail fast
- missing or stale inputs are represented in the report payload rather than in
  ad hoc exit-code conventions

`site-pipeline plan` answers **what local inputs are needed**. It complements
`site-pipeline check`, which answers whether the current workspace and currently
available local inputs are valid and ready for staging.

That planning universe should match the inputs actually consumed by `build` and
`watch`, including consumer-owned top-level site pages, site assets, vendor
asset trees, and component/version-context trees.

That keeps planning visible without turning `build` or `watch` into source-sync
commands.

Planning exit codes should be:

- `0`: planning completed and produced a report, even if entries are `missing`,
  `stale`, or `unresolved`
- `1`: planning completed but found error diagnostics that prevent a usable plan
- `2`: invalid invocation, invalid option combination, or unsupported requested
  report schema version
- `3`: internal failure while attempting to evaluate the workspace

## Recommended `plan` CLI syntax

Recommended forms are:

- `site-pipeline plan --for build`
- `site-pipeline plan --for watch`
- `site-pipeline plan --for build --report-format json --report-schema-version 1`
- `site-pipeline plan --for build --report-format json --report-schema-version 1 --report-output -`
- `site-pipeline plan --for build --report-format json --report-schema-version 1 --report-output .site-pipeline/materialization-report.json`

Recommended flag meanings are:

- `--for` accepts `build` or `watch` and selects the planning target
- `--report-format` accepts `text` or `json`; default is `text`
- `--report-schema-version` selects the machine-readable report schema version
  and is required when `--report-format json` is selected
- `--report-output` selects the report destination; `-` means stdout and is the
  default

## Stable staging commands

`site-pipeline build` and `site-pipeline watch` are the stable stage-producing
commands.

They should:

- use the same resolve-and-validate execution path that `check` uses
- consume the same full local-input universe that `plan` reports, including
  consumer-owned top-level site pages, site assets, vendor asset trees, and
  component/version-context trees
- emit the staged tree and `manifest.json` on successful stage production
- optionally emit machine-readable run reports when requested via the shared
  report flags

Recommended behavior is:

- `build` emits one `StageRunReport` for the completed run
- `watch` rewrites one JSON `StageRunReport` at the selected report-output path
  via same-directory temporary write plus atomic replace after the initial cycle
  and after each subsequent rebuild cycle
- on an ordinary watch-cycle failure that does not invalidate the last finalized
  stage, `watch` keeps running and reports the failed cycle instead of exiting
- if a watch cycle leaves the stage root structurally corrupt, partially
  finalized, or otherwise untrustworthy, `watch` fails hard and exits rather
  than serving a dubious stage
- if the initial cycle cannot produce a trustworthy stage and there is no prior
  trustworthy stage to retain, `watch` exits with code `3` instead of entering
  steady-state watch mode
- `watch --report-format json` requires `--report-output` to be a file path,
  not `-`, because watch mode is long-running and produces repeated cycle
  reports over time

Build exit codes should be:

- `0`: build completed and produced a finalized stage, even if warnings were
  emitted
- `1`: build completed evaluation but found error diagnostics or staging
  failures that prevented a usable finalized stage
- `2`: invalid invocation, invalid option combination, or unsupported requested
  report schema version
- `3`: internal failure or unrecoverable stage-integrity failure

Watch exit codes should be:

- `0`: orderly application-controlled shutdown after the watch loop has started
- `2`: invalid invocation, invalid option combination, or unsupported requested
  report schema version
- `3`: internal failure or unrecoverable stage-integrity failure, including
  cases where the process can no longer guarantee that the current stage root is
  coherent and trustworthy

`watch` should not normally use application-owned exit code `1`; ordinary
per-cycle validation or staging failures should be reported in the refreshed
`StageRunReport` while the process keeps watching for a future successful cycle.
An initial-cycle failure with no trustworthy retained stage is not an ordinary
per-cycle failure; it is a hard failure and therefore exits with code `3`.

If a long-running command is terminated by an external signal, any signal-derived
shell exit status is outside the application-owned `0`-through-`3` contract.

## Recommended `build` and `watch` CLI syntax

Recommended forms are:

- `site-pipeline build`
- `site-pipeline build --report-format json --report-schema-version 1`
- `site-pipeline build --report-format json --report-schema-version 1 --report-output -`
- `site-pipeline build --report-format json --report-schema-version 1 --report-output .site-pipeline/build-report.json`
- `site-pipeline watch`
- `site-pipeline watch --report-format json --report-schema-version 1 --report-output .site-pipeline/watch-report.json`

Recommended flag meanings are:

- `--report-format` accepts `text` or `json`; default is `text`
- `--report-schema-version` selects the machine-readable report schema version
  and is required when `--report-format json` is selected
- `--report-output` selects the report destination; for `build`, `-` means
  stdout and is the default; for `watch`, JSON report output should be a file
  path that the command rewrites after each completed cycle

## Stable outputs API

The stable data-plane API is the staged output contract.

That means downstream consumers should integrate against:

- `manifest.json` as the staged-tree entry point,
- the staged content tree,
- page-local front matter produced by the pipeline,
- aggregate metadata files such as routes, lifecycle, releases, and related
  indexes, and
- the documented staged directory layout.

Renderers and deployment adapters should treat those staged outputs as the
integration boundary rather than reading arbitrary component repositories or
calling internal Python code.

## What is not a public API

The Python implementation is internal.

This means the following are not public or stable APIs:

- Python modules, classes, and functions in the package
- internal build graph or staging internals
- implementation-specific provider integration code
- internal filesystem or watch-loop helpers
- any future plugin or hook machinery unless documented separately as public

Consumers should not import Site Pipeline internals and should assume they may
change at any time.

## `preview` is not part of the stable contract

`preview` is a debugging convenience, not a stable architectural commitment.

It may remain useful for:

- Site Pipeline development,
- staging-contract debugging, or
- consumer integration debugging when no real renderer dev server is available.

But it is intentionally not the main development story. It is not guaranteed to:

- behave like the real published site,
- remain feature-compatible over time, or
- continue to exist indefinitely.

Consumers should not build their local development architecture around
`site-pipeline preview`.

## Why there is no stable `serve` command

The Site Pipeline should not define a stable `serve` command.

A real development server depends on renderer-specific behavior such as:

- how templates are compiled,
- how Markdown, AsciiDoc, Mermaid, or shortcodes are rendered,
- how hot reload works,
- how themes and static assets are resolved, and
- how the dev server watches files and reports errors.

Pulling that into `site-pipeline` would blur the intended architecture by making
the pipeline responsible for rendering concerns it does not own.

That is why a first-class `serve` command is intentionally out of scope for the
core pipeline API.

## Recommended local development pattern

The preferred local development model is:

1. run `site-pipeline watch`,
2. run the consumer's real renderer dev server, and
3. let the renderer react to staged output changes.

This gives developers a realistic preview of the eventual site while preserving
the staging/rendering separation.

Consumer-owned wrappers such as `make serve` are fine when they orchestrate that
workflow, but those wrappers should remain consumer-specific rather than turning
into core Site Pipeline API.

## Relationship to distribution

This contract is intentionally friendly to both:

- an installed Python package that exposes the `site-pipeline` executable, and
- a container image whose entrypoint is `site-pipeline`.

In both cases, callers use the same invocation API and receive the same staged
output contract.

## Future integrations and add-ons

Renderer-specific examples, wrapper scripts, or helper tooling may be useful.

But those should be treated as isolated integrations layered on top of the core
contracts, not as reasons to widen the core API boundary.

## Read next

- [architecture-overview.md](architecture-overview.md) for the high-level system
  picture
- [staged-output-contract.md](staged-output-contract.md) for the staged-tree
  layout and `manifest.json` contract
- [source-resolution-and-materialization.md](source-resolution-and-materialization.md)
  for version selection and materialized content inputs
- [validation-and-check.md](validation-and-check.md) for non-mutating validation,
  diagnostics, and `site-pipeline check`
- [build-architecture.md](build-architecture.md) for the recommended execution
  shape of `build` and `watch`
- [watch-incremental-staging-plan.md](watch-incremental-staging-plan.md) for
  watch guardrails, incremental-staging planning, and implementation milestones
- [security-and-trust-model.md](security-and-trust-model.md) for path-safety,
  trust-boundary, and XSS-defense expectations
- [flexible-component-publication.md](flexible-component-publication.md) for the
  publication and lifecycle model