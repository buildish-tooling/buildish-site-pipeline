---
weight: 13
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

# Staged output contract

This document defines the stable staged-tree contract consumed by renderers,
deployment adapters, and other downstream tooling.

The contract is the stage root itself:

- `manifest.json` as the authoritative entry point
- staged content and static trees
- page front matter attached to staged pages
- aggregate metadata files in `data/*.json`

Consumers should integrate against that staged contract rather than reading
arbitrary repositories or internal Python objects.

## Top-level stage layout

The recommended top-level layout is:

- `manifest.json`
- `content/site/...` for consumer-authored site pages staged by the pipeline
- `content/components/<slug>/...` for component-owned staged pages and docs
- `static/site/...` for consumer-authored site assets staged by the pipeline
- `static/components/<slug>/...` for component assets and opaque static mounts
- `data/*.json` for aggregate metadata

The stage root is renderer-facing. It does not need to mirror source-repository
layout.

## Serialization rules

The serialization contract is:

- page front matter uses YAML
- aggregate metadata uses JSON
- `manifest.json` uses JSON

Optional YAML mirrors for aggregate metadata are outside the core contract. When
they exist, `manifest.json` and `data/*.json` remain authoritative.

## `manifest.json`

`manifest.json` is the authoritative entry point for the staged output contract.

It records:

- the stage-manifest schema version
- the stage-layout version
- the command mode that produced the stage, such as `build` or `watch`
- the relative paths of the top-level content, static, and data roots
- the relative paths of aggregate metadata files that are present

Consumers should read `manifest.json` first and treat it as authoritative for
which aggregate files exist.

## Aggregate metadata inventory

The core aggregate inventory is:

- `data/components.json`
- `data/artifacts.json`
- `data/routes.json`
- `data/redirects.json`

The broader aggregate set may also include:

- `data/releases.json`
- `data/candidates.json`
- `data/refs.json`
- `data/translations.json`
- `data/compatibility.json`
- `data/mounts.json`
- `data/providers.json`
- `data/content-index.json`
- `data/diagnostics.json`

The manifest records which of those files are present for a given stage root.

## Diagnostics

Fatal validation errors stop the build instead of producing a partial stage.

Non-fatal warnings, skipped optional inputs, and stale-provider notices belong in
`data/diagnostics.json` when the pipeline decides they are worth preserving for
downstream tools or operator review.

## Consumer integration patterns

Different downstream consumers can stay focused on the parts they need:

- renderers read staged content, page front matter, and aggregate metadata
- deployment adapters read route and redirect metadata
- search and indexing tools read `data/content-index.json`
- diagnostic or audit tools read `manifest.json` and `data/diagnostics.json`

## Contract rules

The stage contract follows these rules:

- `manifest.json` is authoritative for layout and file presence
- omitted aggregate files mean the corresponding dataset is absent for that stage
- aggregate files must use stable identifiers and public metadata, not machine-
  local implementation details
- builds should write `manifest.json` after aggregate output paths are finalized

## Schema reference

The typed definitions for this contract live in:

- [pipeline-model-schema-reference.md](pipeline-model-schema-reference.md)
  - `StageManifest`
  - `StageRoots`
  - `StageDataFiles`
  - `StageDiagnosticEntry`

## Read next

- [api-contract.md](api-contract.md) for the stable invocation and output
  boundary
- [build-architecture.md](build-architecture.md) for build/watch execution shape
- [security-and-trust-model.md](security-and-trust-model.md) for content-safety,
  path-safety, and trust-boundary rules