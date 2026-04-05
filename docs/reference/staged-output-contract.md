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

Machine-readable command reports for `build` or `watch` may reference the stage
root or manifest location, but they do not replace the staged-tree contract.
`manifest.json` remains the authoritative entry point for downstream consumers.

## Top-level stage layout

The recommended top-level layout is:

- `manifest.json`
- `content/site/...` for consumer-authored site pages staged by the pipeline
- `content/components/<slug>/...` for component-owned staged pages and docs
- `static/site/...` for consumer-authored site assets staged by the pipeline
- `static/site/vendor/<stable-key>/...` for top-level vendor asset trees staged by
  the pipeline
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

## Front matter rules

Authored page front matter remains authored metadata.

Pipeline-owned staged fields should live under a reserved top-level `pipeline`
namespace. In practice that means:

- `pipeline.component` carries pipeline-owned component context when relevant
- `pipeline.page` carries pipeline-owned page-local context when relevant
- authored content must not define the reserved `pipeline` namespace

Collisions with the reserved namespace are validation errors.

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

Consumers should also treat `manifest.json` as a coordination and publication-
boundary document, not as an ordinary renderer data file. It is written last for
each finalized stage publication, so successful `build` and `watch` updates may
change it even when a renderer would otherwise keep using the same staged pages
and aggregate payloads. Renderers should normally read staged pages and
`data/*.json` instead of importing `manifest.json` into templates or normal
site-data processing.

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

When `data/content-index.json` includes `sourcePath`, that path must be a
repo-relative authored source path. Generated or imported staged content that has
no workspace-authored source file should omit `sourcePath` instead of exposing a
machine-local path.

For route and redirect consumers, the key distinction is:

- `data/routes.json` describes the public route surface the stage owns
- `data/redirects.json` describes concrete redirect responses that should be
  emitted for incoming requests

Within `data/routes.json`, `section` identifies the publication surface such as
`component`, `development`, `docs`, or `released`, while `routeKind`
identifies the route class such as `published`, `context`, or `alias`. The
separate `canonical` flag identifies the preferred published route for a target.

Concrete redirect behavior does not live on route rows. It is emitted in
`data/redirects.json` with resolved `fromUrl`, `toUrl`, `status`, optional
`reason`, and optional `sourceKind` metadata.

## Diagnostics

Fatal validation errors stop the build instead of producing a partial stage.

The same trust rule should apply to watch-triggered rebuilds. If a failed cycle
cannot preserve the previously finalized stage as a coherent contract surface,
the watch process should exit instead of continuing with a corrupt or ambiguous
stage root.

Non-fatal warnings, skipped optional inputs, and stale-provider notices must be
written to `data/diagnostics.json` when they are present in a finalized stage.
The file may be omitted only when the finalized stage has no preserved non-fatal
diagnostics.

When diagnostic detail payloads need size reduction, `data/diagnostics.json`
must still remain complete, valid JSON. Implementations must preserve the
diagnostic entry and replace only the oversized `details` payload with a bounded
summary object, informally called `ReducedDiagnosticDetailsSummary`, rather than
writing a partial or malformed file. The recommended summary fields are
`omitted`, `reason`, `actualBytes`, `limitBytes`, optional short `summary`, and
optional `fingerprint`.

`site-pipeline check` may emit the same machine-readable diagnostic entry shape
directly without producing a stage tree.

`site-pipeline build` and `site-pipeline watch` may also emit machine-readable
run reports when requested, but those reports are operator/automation aids on
top of the stage contract rather than substitutes for it.

Public aggregate files and machine-readable reports must not leak private
machine-local paths. Workspace-authored paths may be rewritten to repo-relative
form, while private work or stage roots must be redacted.

## Consumer integration patterns

Different downstream consumers can stay focused on the parts they need:

- renderers read staged content, page front matter, and aggregate metadata;
  they use `manifest.json` only to discover the stage layout and available data
  files
- deployment adapters read route and redirect metadata and can turn them into
  concrete HTTP server or CDN config as described in
  [../how-to/http-server-config-how-to.md](../how-to/http-server-config-how-to.md)
- search and indexing tools read `data/content-index.json`
- diagnostic or audit tools read `manifest.json` and `data/diagnostics.json`

## Contract rules

The stage contract follows these rules:

- `manifest.json` is authoritative for layout and file presence
- `manifest.json` is a control-plane entry point and publication marker, not a
  normal renderer template/data input
- omitted aggregate files mean the corresponding dataset is absent for that stage
- aggregate files must use stable identifiers and public metadata, not machine-
  local implementation details
- if a finalized stage contains preserved non-fatal diagnostics,
  `data/diagnostics.json` must be present
- finalized aggregate files and machine-readable report files must be written
  via same-directory temporary files followed by atomic replace
- implementations must reject output targets that escape the owned stage or
  report root, or whose final write path resolves through a symlink
- builds must write `manifest.json` last and replace it atomically only after
  referenced output paths are finalized
- watch rebuilds should either preserve the last trustworthy finalized stage or
  exit; they should not knowingly continue with a stage root whose integrity is
  uncertain

## Schema reference

The typed definitions for this contract live in:

- [pipeline-model-schema-reference.md](pipeline-model-schema-reference.md)
  - `StageManifest`
  - `StageRoots`
  - `StageDataFiles`
  - `PipelineDiagnosticEntry`

## Read next

- [api-contract.md](api-contract.md) for the stable invocation and output
  boundary
- [../architecture/build-architecture.md](../architecture/build-architecture.md) for build/watch execution shape
- [security-and-trust-model.md](security-and-trust-model.md) for content-safety,
  path-safety, and trust-boundary rules