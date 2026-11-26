---
title: "Staged output contract"
description: "This document defines the stable staged-tree contract consumed by renderers, deployment adapters, and other downstream tooling."
weight: 13
---

<!--
Copyright 2026 The Buildish Authors

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
- `content/<resolved-public-path>/...` for component-owned staged pages and docs,
  using the same normalized public hierarchy that route metadata advertises
- `static/site/...` for consumer-authored site assets staged by the pipeline
- `static/site/vendor/<stable-key>/...` for top-level vendor asset trees staged by
  the pipeline
- `static/<resolved-public-path>/...` for component-owned static output, including
  component asset trees and context-owned static mounts
- `data/*.json` for aggregate metadata

The stage root is renderer-facing. It does not need to mirror source-repository
layout. Component-owned staged paths should therefore track the resolved public
paths instead of an internal taxonomy such as `contexts/...`.

## Serialization rules

The serialization contract is:

- page front matter uses YAML
- aggregate metadata uses JSON
- `manifest.json` uses JSON

Optional YAML mirrors for aggregate metadata are outside the core contract. When
they exist, `manifest.json` and `data/*.json` remain authoritative.

## Page input detection and routed paths

Page input support is extension allow-list based.

The pipeline currently treats files ending in `.md`, `.markdown`, `.mdx`,
`.htm`, `.html`, `.adoc`, or `.asciidoc` as authored page inputs. Those files
are handled generically as text content plus optional YAML front matter. The
pipeline does not validate renderer-specific Markdown or AsciiDoc syntax.

For routed public paths, `index.<supported-page-extension>` is treated as the
directory index page. For non-index pages, the pipeline drops the suffix for
`.md`, `.markdown`, `.mdx`, `.adoc`, and `.asciidoc`, while `.htm` and `.html`
keep their filename suffix in the routed public path.

## Front matter rules

Authored page front matter remains authored metadata.

Pipeline-owned staged fields should live under a reserved top-level `pipeline`
namespace. In practice that means:

- `pipeline.component` carries pipeline-owned component context when relevant
- `pipeline.page` carries pipeline-owned page-local context when relevant
- authored content must not define the reserved `pipeline` namespace

Collisions with the reserved namespace are validation errors.

The staged document therefore has two owners. Fields outside `pipeline`, such
as `title`, `description`, or renderer-specific navigation settings, remain the
author's data. The coordinator derives `pipeline` fields for each stage and
overwrites coordinator-owned values when retained incremental metadata is
normalized. Consumers may rely on the typed staged values; authors must not
copy them into source pages.

`pipeline.component` provides component-wide identity, resolved publication
roots, and compact artifact or release summaries. `pipeline.page` provides the
current page's normalized route and kind, optional localization and translation
links, version and provider context, and optional source provenance. This lets
renderers build navigation, version selectors, canonical links, localization
controls, status badges, and source links without reconstructing the build
plan.

When `pipeline.page.source` is present:

- `key` identifies the named binding supplying the physical input
- `path` is relative to the emitted original `repository`, or to the binding root
  for a local-only direct page; it is not a workstation or staged-copy path
- `repository` is the declared target repository, which may differ from the
  materialization binding's repository
- `viewRef` is the exact declared view revision; tags and named refs may move
- `editRef` is present only for supported direct same-file editing targets

For exported docs, a selected provider record's explicit `docsSource` supplies the
original repository, docs root and revision. The producer asserts a tree-preserving
export. Releases, candidates, maintenance and named-ref materializations without
this mapping omit source provenance; mapped docs omit edit links. Static and direct
development pages retain declared branch links. Consumers must not replace missing
values with `main` or a site repository.

Local-only named direct sources may provide only `key` and `path`. Synthetic
component shorthand and sources outside the owned input/binding omit provenance.
The coordinator recomputes provenance for both fresh and retained contributions,
matching their owning unit, artifact and exact source/destination file association.
It does not trust worker-supplied source targets or version labels for this choice.
Consumers construct host-specific URLs and escape paths/refs themselves. A direct
binding's declared repository must correspond to its repository root; `docsSource`
explicitly names the original root for a rematerialized docs tree.

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

## Explicit release recommendations and destinations

Each artifact row in `data/artifacts.json` contains required `releaseDesignations`.
The row's `componentSlug` and `key`, together with a target's exact `version`,
identify one released artifact. Overall `latestStable` and each `lines[].target`
come from explicit component/snapshot facts. A deliberately older recommendation
is valid; selection never replaces it with a maximum or a development version.
The old inferred `latestRelease` field and `LatestReleaseSummary` type are removed.
Consumers needing recommendations must read this view; selected release rows
remain available for descriptive listings. No compatibility alias is emitted.

<!-- test:release-designation-artifact -->
```json
{
  "componentSlug": "spark",
  "key": "runtime",
  "latestStable": "4.0.1",
  "releaseLines": [{"key": "4.0", "latest": "4.0.1"}],
  "releaseDesignations": {
    "snapshotStatus": "present",
    "latestStable": {
      "version": "4.0.1",
      "selected": false,
      "publicationState": "published",
      "availability": {"kind": "unavailable", "reason": "not-selected"}
    },
    "lines": [{
      "key": "4.0",
      "target": {
        "version": "4.0.1",
        "selected": false,
        "publicationState": "published",
        "availability": {"kind": "unavailable", "reason": "not-selected"}
      }
    }]
  }
}
```

This example can result from selecting 4.0.0 while recommending 4.0.1. No target
is staged merely to populate this view. The raw `latestStable`/`releaseLines`
strings remain compact mirrors, including in front matter; resolved availability
exists only in the artifact aggregate.

`snapshotStatus` describes the configured component snapshot input: `present`,
`missing` (successful optional-input stages), or `not-configured`. It does not
promise complete historical inventory. An absent optional snapshot supplies no
recommendation facts; an explicit site pin does not invent them. Curated releases
inside a present normalized snapshot need no provider record. Required inventory
absence and selected missing docs retain existing input-error behavior.

`latestStable` is omitted when no overall recommendation exists. `lines` is always
a list, possibly empty; parent/child lines sharing one version retain both pointers.
`selected` means desired site selection, before visibility filtering. An explicit
`publicationState` is preserved even when unselected; absent state is not silently
labelled published. Only selected targets have `action` (`docs`, `omit`, `notice`
or `redirect`). Conflicting facts and ambiguous provider matches for selected or
designated targets prevent successful publication, even if a site pin excludes
the ambiguous recommendation. Unrelated unselected history is not newly ordered.

| `availability.kind` | Fields and meaning |
| --- | --- |
| `docs` | `path`, `url`: a reconciled root documentation page owned by this exact artifact/version. |
| `notice` | `path`, `url`: a reconciled generated withdrawal notice, not original docs. |
| `redirect` | `path`, `url`, `toUrl`: an emitted withdrawal redirect instruction for the deployment adapter; replacement content is not attested. |
| `unavailable` | `reason` only; no destination fields. |

Unavailable reasons are `not-selected` for excluded targets; `hidden`, `withdrawn`,
`tombstoned`, `snapshot-absent` or `omitted` for selected omissions; and
`no-landing-page` for selected docs without an eligible owned root. Unselected
state is retained separately from the `not-selected` reason. Descendants, assets,
a renderer-generated section, or another artifact's shared root cannot establish
this artifact's landing page. Only an unlocalized or configured-default-locale
root at the exact context path qualifies; no alternate-locale fallback is chosen.

Destination paths use the resolved P03 artifact routes, including explicit flat
defaults. Eligibility is checked after current destination/file reconciliation for
fresh and retained contributions. It describes a successful Pipeline stage, not
Hugo rendering, remote deployment, reachability or content completeness. Only
`kind: docs` satisfies a docs link request. Never use route presence alone,
notices, redirects or development docs as a substitute.

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

When a `data/content-index.json` entry includes `source`, it uses the same
structured source-provenance object as `pipeline.page.source`. Its `path` is
relative to the original target repository (or the binding for a local-only direct
page), and repository/ref fields are optional.
Generated, imported, shorthand-local, or out-of-binding staged content that has
no safe public provenance omits `source` instead of exposing a workspace or
machine-local path.

For example:

```json
{
  "id": "spark-runtime-4.0.0-index",
  "componentSlug": "spark",
  "artifactKey": "runtime",
  "pageKind": "release-page",
  "originKey": "docs",
  "path": "/spark/releases/4.0.0",
  "url": "https://docs.example.org/spark/releases/4.0.0/",
  "source": {
    "key": "runtime",
    "path": "docs/index.md",
    "repository": "https://github.com/example/runtime",
    "viewRef": "v4.0.0"
  },
  "versionKind": "released",
  "versionLabel": "4.0.0"
}
```

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
  [http server config how to](../../../how-to/http-server-config-how-to/)
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

## Artifact routes and destination ownership

`pipeline.component.publication` and the component aggregate expose
`artifactRouting` (`shared` or `namespaced`) and optional `defaultArtifact`.
Their component paths/URLs remain layout bases. Concrete artifact/context paths
are carried by page version metadata, routes and refs; there is no synthesized
artifact landing page. Page-local componentPath/componentUrl keep pointing at the
component itself. A default artifact's flat destination is primary, with no second
docs tree. Notices and redirects retain source routes without usable docsPath or
docsUrl or copies of excluded original files.

Pages, docs-tree non-pages and contextual assets use the same effective context
route: content files stay under `content/`, while contextual assets use `static/`.
Component assets retain the independent component assetsPath. Original-source
links derive from the owned physical source/file/context association, independently
of the public namespace.

Before copying and before publication, the pipeline rejects conflicting producer
claims for stage files and rendered destinations, including duplicates within one
component worker. Disjoint shared trees remain supported. Complete candidate
content/static inventories are reconciled against current claims, including retained
files: directory ownership alone cannot authorize an unexpected descendant.
A failed candidate preserves the last trustworthy visible stage. Rebuilding the
affected unit removes stale retained files through the existing watch mechanism.

Renderers adopting namespaced routes must use the declared mode/default and concrete
artifact routes for navigation. Component paths.docs may be an absent layout base;
it is not a fallback documentation target. Richer designation availability is a
separate contract concern.

## Generated release-notes pages

A released provider record may declare `releaseNotes.path`. When that release's
context stages original docs, the pipeline generates one page below the context
route, for example `/spark/releases/4.0.0/release-notes`:

- the segment defaults to `release-notes`; a component's catalog `publication`
  may set `releaseNotesSegment` and `releaseNotesTitle`
- front matter has a pipeline-generated `title` only; the notes file is the body,
  unchanged
- `pipeline.page.kind` and the content-index `pageKind` are `release-notes`, and
  `section` is the context's section (`release`)
- the page carries no `source` provenance; provider provenance is kept
- `data/releases.json` rows gain `releaseNotes` (`path`, `url`) only when the page
  was staged in this output

Development, candidate, notice, redirect, omitted and site-excluded contexts never
get a notes page. In `shared` artifact routing, at most one artifact may declare
notes for one shared version context; only its `releases.json` row carries
`releaseNotes`. Docs pages and assets at or beneath the notes route conflict with
the generated page. Renderers link to notes from `releaseNotes.path` or `url` and
must not derive the route from the segment. Keep the segment unchanged once notes
are published: changing it moves every published notes route without aliases or
redirects.

## Schema reference

The typed definitions for this contract live in:

- [pipeline-model-schema-reference.md](../pipeline-model-schema-reference/)
   - `StageManifest`
   - `StageRoots`
   - `StageDataFiles`
   - `PipelineDiagnosticEntry`
- [pipeline-staged-front-matter-reference.md](../pipeline-staged-front-matter-reference/)
  for the complete `pipeline.component`, `pipeline.page`, and source-provenance
  field contracts

## Read next

- [api-contract.md](../api-contract/) for the stable invocation and output
   boundary
- [build architecture](../../../architecture/build-architecture/) for build/watch execution shape
- [security-and-trust-model.md](../security-and-trust-model/) for content-safety,
   path-safety, and trust-boundary rules
