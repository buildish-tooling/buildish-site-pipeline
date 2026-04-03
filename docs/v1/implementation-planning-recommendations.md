---
weight: 41
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

# Implementation planning recommendations

This document records the planning questions that were evaluated before
implementation work and the recommended defaults chosen for the current design.

The core publication and staged-output model now looks sound. The sections below
focus on resolution details, integration boundaries, and operator-facing
behavior.

Each section includes a recommended default so implementation planning can move
forward deliberately instead of inventing local rules ad hoc.

## What this list is for

These are not reasons to throw away the current model.

They are the places where an implementation plan will be cleaner if the design is
made explicit first.

## 1. Site-level authored content and vendor assets

The staged-output contract and schema now define explicit top-level site content
and vendor-asset input configuration.

The remaining implementation question is how collision handling composes with
component-owned content.

Implementation should make the following rules explicit:

- how collisions are resolved against component-owned staged output
- whether site-owned content or component-owned content wins for the same final
  public path
- how collision diagnostics are reported to operators

### Recommended direction

Add one explicit consumer-owned top-level site-content section in the main
workspace configuration rather than hiding site pages and site assets inside the
component model.

Recommended shape:

- one place for site page roots
- one place for site asset roots
- one place for vendor/imported top-level asset declarations
- explicit collision rules against component-owned output

Pros:

- keeps site-wide content clearly separate from component-owned content
- makes root-page ownership obvious
- gives the build planner one authoritative place to find non-component inputs

Cons:

- introduces another authored configuration section
- makes the "tiny site" story slightly less minimal

### Other viable options

#### Option A: convention-only site roots

Infer site pages and assets from fixed conventional directories.

Pros:

- lowest initial configuration cost

Cons:

- weak for multi-site or non-standard layouts
- pushes too much behavior into undocumented convention

#### Option B: separate site workspace document

Put site-level content in a second dedicated config document.

Pros:

- very clean separation of concerns

Cons:

- adds one more file and one more merge boundary
- likely heavier than needed for the first implementation wave

## 2. Explicit local override layer for provider data

Several docs assume that consumers may sometimes need a narrow local override
layer for provider-derived facts.

The remaining question is whether that override layer is part of the initial
design or a later extension.

This needs a decision on:

- whether override files exist at all in the first implementation wave
- where they live
- what fields they may override
- exact precedence against provider snapshots and authored metadata

### Recommended direction

Do **not** make override files part of the first implementation wave unless a
real consumer is already blocked on them.

Instead, keep the extension point explicit in the docs and implementation shape,
but treat provider overrides as a later, narrow, auditable feature.

Pros:

- avoids inventing a second truth source too early
- keeps provider merge rules simpler in the first wave
- reduces schema and validation surface area

Cons:

- a few real-world corrections may require manual provider snapshot fixes at
  first
- some consumers may want the override layer sooner than later

### Other viable options

#### Option A: introduce a narrow override file now

Allow only a small set of provider-derived fields to be corrected locally.

Pros:

- solves real data-cleanup cases early
- preserves an auditable local correction path

Cons:

- adds precedence complexity immediately
- easy to over-expand once the mechanism exists

#### Option B: allow broad override files now

Pros:

- maximum flexibility

Cons:

- strongly discouraged; too easy to blur authored truth and provider truth
- increases long-term maintenance and debugging cost

## 3. Authored page metadata vs pipeline-owned front matter

Translation linkage is intentionally page-authored, while staged front matter is
pipeline-owned.

The remaining question is how authored page metadata is carried into staged pages
without leaving merge behavior implicit.

This needs a decision on:

- whether authored front matter is preserved verbatim, filtered, or normalized
- whether pipeline-owned data always lives under a reserved namespace
- what happens on field collisions between authored metadata and pipeline fields

### Recommended direction

Preserve authored page metadata, but emit all pipeline-owned page data under a
reserved namespace and fail if authored content attempts to occupy that reserved
namespace.

That keeps authored metadata and pipeline metadata adjacent without making merge
semantics guessy.

Pros:

- very predictable for renderers and content authors
- avoids silent field clobbering
- keeps future pipeline enrichment additive

Cons:

- produces slightly more nested front matter
- some templates may need to read both authored and pipeline-owned sections

### Other viable options

#### Option A: flatten pipeline fields into top-level front matter

Pros:

- compact staged pages

Cons:

- high collision risk
- hard to evolve safely over time

#### Option B: normalize and selectively copy authored metadata

Pros:

- smaller staged front matter

Cons:

- easier to surprise authors
- requires a more opinionated authored-metadata policy up front

## 4. Effective configuration resolution rules

The docs now describe defaults, groups, component overrides, and artifact
overrides as one explicit resolution algorithm.

The remaining implementation task is to apply that algorithm consistently.

Implementation should exercise and verify:

- defaults vs group vs component precedence
- merge vs replace semantics for nested objects and arrays
- how support-status vocabularies are overridden or narrowed
- how localization overrides compose

### Recommended direction

Define one simple explicit resolution algorithm:

- precedence: `defaults` < `group` < `component` < `artifact`
- scalar values: nearest defined value wins
- maps/objects: merge by key, with the nearer level winning per key
- arrays/lists: replace rather than concatenate
- absent values inherit; explicitly empty arrays/maps clear inherited values

Pros:

- easy to explain and implement
- reduces surprising duplication from implicit list concatenation
- gives validation one deterministic effective-config view

Cons:

- some consumers may eventually want append/merge semantics for arrays
- explicit clearing needs to be documented carefully

### Other viable options

#### Option A: deep-merge everything possible

Pros:

- feels flexible at first

Cons:

- difficult to predict
- high risk of accidental inheritance bugs

#### Option B: replace everything at each level

Pros:

- maximally simple implementation

Cons:

- too verbose for real configs
- discourages useful shared defaults

## 5. Grammar for string-based internal references

Several important fields are still strings that refer to structured internal
objects, for example redirect targets and compatibility references.

The remaining question is whether the design wants a small explicit reference
grammar or a more typed schema expansion.

This needs a decision on:

- syntax for internal redirect targets
- syntax for compatibility `subjectRef` and `targetRef`
- whether exact releases, lines, artifacts, and routes use one shared selector
  grammar or several typed fields

### Recommended direction

Keep the fields as strings for now, but define a small typed reference grammar so
they stop behaving like free-form text.

For example, use typed prefixes such as:

- `route:/docs/latest/`
- `component:spark`
- `artifact:spark/runtime`
- `line:spark/runtime@4.x`
- `release:spark/runtime@4.0.0`

Pros:

- small schema change surface
- easy to validate incrementally
- readable in authored config and aggregate metadata

Cons:

- still stringly typed compared with a fully structured union
- requires one more tiny reference-language spec

### Other viable options

#### Option A: expand into typed union objects now

Pros:

- strongest validation and editor tooling potential

Cons:

- larger schema change
- heavier authoring syntax

#### Option B: leave strings unconstrained for now

Pros:

- lowest short-term effort

Cons:

- not recommended; pushes ambiguity into every consumer and validator

## 6. Locale routing details

Locale-aware publication is now clearly part of the model, but the exact route
derivation rules are still lighter than the rest of the routing design.

The remaining question is how the currently supported route modes, default-
locale behavior, and partial translation coverage interact in detail.

This needs explicit implementation rules for:

- exact path derivation for `none` and `prefixAll`
- default-locale and fallback behavior when translation coverage is partial
- how aliases and redirects behave in localized publication

### Recommended direction

For the first implementation wave, fully specify and prioritize only:

- `none`
- `prefixAll`

Treat host-per-locale publication as a later extension rather than part of the
initial contract.

Also document these first-wave rules explicitly:

- route derivation happens before alias/redirect generation
- missing translations do not synthesize sibling pages
- fallback locale is for renderer behavior, not silent route generation

Pros:

- lowers the first-wave implementation surface
- covers the most common multilingual publication shape
- avoids overbuilding before real localized consumers exercise the model

Cons:

- host-per-locale users may need a second implementation wave
- docs must clearly mark that host-per-locale publication is later work

### Other viable options

#### Option A: implement all route modes immediately

Pros:

- broad theoretical completeness

Cons:

- larger test matrix
- higher risk of unresolved edge cases around redirects and aliases

## 7. Stable planning/report command

The design clearly wants a report-only planning step and a machine-readable
materialization report.

The recommended settled direction is to treat both the planning command and the
machine-readable report shape as stable surface.

Recommended behavior:

- the stable command is `site-pipeline plan`
- planning returns exit code `0` when it successfully produced a report, even if
  inputs are missing, stale, or unresolved
- exit code `1` means planning found error diagnostics that prevent a usable plan
- exit code `2` means invalid invocation, invalid option combination, or
  unsupported requested report schema version
- exit code `3` means internal failure
- missing/stale/unresolved states live in the report payload, not in ad hoc exit
  code conventions

Why this is the recommended contract:

- automation-friendly
- keeps wrappers from needing special case logic per missing-input state
- lets the command and report become durable integration boundaries
- aligns the planning surface with the now-explicit `check`, `build`, and
  `watch` command set

## 8. Operational limits and abuse resistance

The security model now distinguishes between hard non-overridable security
ceilings and safe operational defaults. Treat
`security-and-trust-model.md` as the canonical source for the current values.

The current split is:

- mounted metadata payload: 16 KiB per serialized `metadata` object
- diagnostic detail payload: 8 KiB per serialized `details` object
- provider snapshot input default: 16 MiB JSON and 50,000 normalized
  `records[]` entries
- route inventory default: 100,000 entries
- redirect inventory default: 100,000 entries
- content index default: 100,000 entries
- watch scope default: 32 roots and 100,000 filesystem entries at startup
- staged version contexts default: 512 per run

Failure behavior for hard ceilings should stay fail-fast and machine-readable.
The remaining design question is the local override surface for safe defaults.
That surface should stay local to execution policy and may later be expressed as
explicit numbers, a t-shirt-size profile, or another local mechanism. It should
remain operator-controlled rather than coming from provider data or repo-authored
publication metadata.

## Recommended use during planning

Implementation planning can start now, but these questions should be treated as
explicit planning inputs rather than left to incidental implementation choice.

If they remain unresolved, different workstreams may otherwise make incompatible
assumptions about the same design boundary.