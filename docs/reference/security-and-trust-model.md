---
weight: 16
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

# Security and trust model

This document defines the baseline security posture for the current model.

The Site Pipeline stages and normalizes content. It does not make untrusted
content safe by accident. Safety depends on explicit validation, careful staged
metadata design, renderer escaping, and clear treatment of mounted active
content.

## Core principles

The baseline rules are:

- metadata strings are untrusted text unless a field explicitly says otherwise
- path-bearing inputs must stay within declared source or materialization roots
- aggregate outputs must avoid machine-local implementation details
- imported active HTML/JS content is trusted code, not inert content
- renderers must escape metadata by default

## Path and filesystem safety

Path-bearing inputs include authored content roots, metadata files, local source
roots, mount sources, and materialized local trees.

The pipeline must:

- normalize every path before use
- resolve symlinks before trust decisions are made
- reject any path that escapes its declared root after normalization
- reject archive extraction or bundle expansion that would write outside an owned
  destination
- validate report-output and stage-finalization destinations before writing
- reject output targets whose final write path resolves through a symlink or
  escapes the owned output root
- require candidate stage roots to be real directories that are absent or empty,
  never symlinks and never pre-populated with leftover content
- avoid publishing symlink escapes into the staged tree

This protects against accidental workspace leakage and straightforward path
traversal mistakes.

## Metadata and XSS safety

The model intentionally allows many human-facing string fields, including titles,
labels, descriptions, notes, and provider metadata.

The safety rule is simple:

- those values are data, not trusted HTML

That means:

- the pipeline preserves them as structured text
- renderers HTML-escape them by default
- templates should treat raw HTML rendering as an explicit opt-in outside the
  core pipeline contract

## URL and redirect safety

Redirects and other URL-bearing fields need validation in addition to schema
shape checks.

The pipeline must:

- require internal redirect targets to resolve to known internal routes
- reject unsupported URL schemes such as `javascript:` and `data:`
- treat external redirect destinations as explicit policy decisions
- prefer `https` for public external destinations

Local development tooling may allow additional schemes only by local
operator-controlled development policy that stays outside the default pipeline
contract and outside repo-authored or provider-authored inputs.

## Mounted content trust classes

Mounted content falls into three broad classes:

- pipeline-rendered markup and pages
- inert static assets such as images, archives, or downloadable files
- imported active site trees containing HTML, CSS, or JavaScript

The first two are normal publication inputs.

Every mounted subtree should declare a machine-readable `trustClass`:

- `passive` for pipeline-rendered content and inert static assets
- `active` for imported browser-executable HTML/JS/CSS trees

Imported active site trees are different. They are trusted code with the ability
to execute in the browser and influence same-origin behavior.

Consumers publishing imported active site trees should decide deliberately:

- whether the subtree shares the main origin
- whether it needs path or host isolation
- which CSP, cookie, and storage policies apply at deployment time

The pipeline can stage and describe those mounts, but it should not pretend they
are inert. `trustClass: active` is the signal deployment adapters should use to
apply isolation and stricter policy.

## Aggregate-output minimization

Public staged outputs should prefer stable identifiers, public paths, and public
URLs over machine-local details.

Aggregate metadata should avoid exposing:

- absolute local filesystem paths
- cache-internal directory layout
- internal-only provider endpoints or non-public provider base URLs
- other machine-local implementation details

## Resource-exhaustion and abuse resistance

The pipeline should remain defensive against oversized or abusive inputs.

The model should distinguish between hard non-overridable security ceilings and
safe operational defaults.

### Hard non-overridable security ceilings

These ceilings are part of the abuse-resistance posture itself. Implementations
must reject rather than silently truncate when they are exceeded, except for the
special `PipelineDiagnosticEntry.details` reduction rule documented below.

- mounted metadata payload size: at most 16 KiB per `metadata` object after JSON
  serialization
- diagnostic detail payload size: at most 8 KiB per
  `PipelineDiagnosticEntry.details` object after JSON serialization

Oversized diagnostic details need special handling because operators still need
to understand the failure. Implementations must therefore keep the diagnostic
entry itself, including its `severity`, `code`, `message`, and any available
`componentSlug`, `artifactKey`, or `targetId`, and replace only the oversized
`details` payload with a bounded summary object, informally called
`ReducedDiagnosticDetailsSummary`. The recommended replacement shape is:

- `omitted: true`
- `reason: sizeLimitExceeded`
- `actualBytes`
- `limitBytes`
- optional short `summary`
- optional `fingerprint`

That `ReducedDiagnosticDetailsSummary` should say that details were reduced
because of the ceiling, include the measured and allowed sizes, and may include
a compact summary or fingerprint. Implementations must never respond by
emitting malformed or partial JSON diagnostic files.

### Safe operational defaults

These values are conservative initial defaults for ordinary installations. They
are execution-policy settings rather than public staged-output contract shape.
Implementations may allow local operator override of these defaults. The
override mechanism is intentionally not fixed here and may later be an explicit
number, a t-shirt-size profile, or another local policy surface.

That override surface must remain local operator-controlled execution policy. It
must not come from provider data, and it must not be driven by repo-authored
publication metadata.

- provider snapshot input default: 16 MiB of JSON and 50,000 normalized
  `records[]` entries in one loaded snapshot
- route inventory default: 100,000 entries in `data/routes.json`
- redirect inventory default: 100,000 entries in `data/redirects.json`
- content index default: 100,000 entries in `data/content-index.json`
- watched directory scope default: 32 watch roots and 100,000 filesystem
  entries beneath those roots at watch startup
- staged version-context count default: 512 in one run

When an implementation exposes local overrides for those defaults, they must not
change the staged output schema or other public contract surfaces.

Failure behavior should be explicit and fail fast when a hard ceiling other than
the `PipelineDiagnosticEntry.details` ceiling is exceeded. Exceeding a safe
operational default should also produce a clear error diagnostic unless the
local operator configuration has intentionally raised that default. Where
practical, limit-hit diagnostics should report the measured and allowed values
and indicate whether the effective threshold came from the documented default or
a local operator override.

For avoidance of doubt: exceeding the `PipelineDiagnosticEntry.details` ceiling
does not justify dropping the whole diagnostic entry or writing incomplete JSON.
The reduction applies only to the oversized `details` payload, not to the
operator-essential diagnostic identity.

## Responsibility split

Security is shared across layers:

- the pipeline validates, normalizes, and rejects unsafe structural inputs
- renderers escape metadata and handle safe HTML rendering policy
- deployment adapters and site operators enforce origin isolation, CSP, and
  server policy for active mounted content

## Read next

- [flexible-component-publication.md](flexible-component-publication.md) for the
  publication model and validation rules
- [staged-output-contract.md](staged-output-contract.md) for the staged-tree
  contract
- [../architecture/source-resolution-and-materialization.md](../architecture/source-resolution-and-materialization.md)
  for local input and cache boundaries