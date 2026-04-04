---
weight: 27
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

# Provider snapshot to staged metadata mapping

This document describes how normalized provider snapshot data should flow into
staged metadata. It complements `provider-snapshot-schema.md` by answering not
just what a provider may supply, but what the pipeline should emit for renderers.

## Mapping principles

- authored metadata remains authoritative for identity, routing, content roots,
  publication selection, and exact-release publication behavior
- provider metadata enriches lifecycle, release, candidate, ref, and asset state
- page front matter should contain only page-local and immediately relevant
  context
- aggregate files in `data/` should contain cross-page and cross-component query
  data
- provider-specific details outside the normalized contract should stay out of
  the public staged outputs for now rather than being copied through wholesale

## Staged outputs overview

Recommended staged outputs that may receive provider-derived data:

- page front matter
- `data/providers.json`
- `data/components.json`
- `data/artifacts.json`
- `data/releases.json`
- `data/candidates.json`
- `data/refs.json`
- `data/content-index.json`

## Serialization format recommendation

Page front matter commonly uses YAML, but aggregate metadata needs a more
portable baseline for renderer and tooling integration.

In practice:

- Markdown front matter is commonly YAML across mainstream documentation tools
- aggregate data-file support varies more across renderers and site generators
- JSON is the safest baseline format for machine-consumed staged metadata

Recommended rule:

- keep page front matter YAML
- emit aggregate staged metadata in JSON as the contract format
- treat optional alternate serializations as non-authoritative mirrors

## What goes into page front matter

Page front matter should expose only what is needed to render the current page
and closely related navigation affordances.

Pipeline-owned staged values should live under the reserved top-level
`pipeline.page` namespace so authored page metadata and pipeline metadata do not
collide silently.

Recommended provider-derived fields in page front matter:

- `provider`
- `externalId`
- `externalUrl`
- `version.kind`
- `version.label`
- optional `version.tag`
- optional `version.ref`
- optional `version.maturity`
- optional `version.releaseLine`
- optional `version.releaseLineAncestors`
- optional `version.supportStatus`
- optional `version.candidateSequence`
- optional `version.voteStatus`

These values should be present only when the page belongs to a provider-backed
release, candidate, or named ref context.

Example page-level shape:

```yaml
pipeline:
  page:
    artifactKey: runtime
    version:
      kind: candidate
      label: 4.1.0-rc2
      maturity: rc
      releaseLine: 4.x
      candidateSequence: 2
      voteStatus: open
    provider:
      key: atr
      externalId: atr:candidate:spark-runtime:4.1.0:2
      externalUrl: https://release-test.apache.org/candidates/spark-runtime/4.1.0/2
```

## What belongs in aggregate metadata

Anything that must be queried across pages, components, or artifacts should be
written to `data/` files instead of repeated into front matter.

### `data/providers.json`

Purpose:

- inventory of loaded providers
- fetch timestamps and provenance
- diagnostics for stale or missing provider data

Recommended fields:

- `key`
- `type`
- optional `displayName`
- optional public `baseUrl` when safe to disclose
- `fetchedAt`

### `data/components.json`

Provider data should influence component summaries only when it is useful to show
derived lifecycle state at component level.

Recommended provider-derived additions:

- latest published release per artifact
- latest candidate per artifact
- available provider keys for the component

The full release inventory should not be duplicated here.

### `data/artifacts.json`

This should be the main aggregate view for artifact-level lifecycle and version
state.

Recommended provider-derived fields:

- `providerKeys`
- `latestRelease`
- `latestCandidate`
- `releaseLines[]`
- `namedRefs[]`

Each `releaseLines[]` entry may include:

- `key`
- optional `parent`
- optional `latest`
- optional `supportStatus`
- optional `headRef`

### `data/releases.json`

Purpose:

- one normalized entry per exact released version
- source for release listings, version selectors, and download pages

Recommended fields:

- `provider`
- `externalId`
- `externalUrl`
- `componentSlug`
- `artifactKey`
- `version`
- optional `displayVersion`
- optional `tag`
- optional `releaseLine`
- optional `releaseLineAncestors`
- optional `supportStatus`
- optional `publicationState`
- optional `withdrawalBehavior`
- optional `redirectTarget`
- optional `maturity`
- optional `publishedAt`
- optional `assets`
- optional `urls`

### `data/candidates.json`

Purpose:

- one normalized entry per in-flight or historical release candidate
- source for vote pages, candidate listings, and release-vote UIs

Recommended fields:

- `provider`
- `externalId`
- `externalUrl`
- `componentSlug`
- `artifactKey`
- `version`
- optional `displayVersion`
- optional `candidateSequence`
- optional `releaseLine`
- optional `maturity`
- optional `voteStatus`
- optional `createdAt`
- optional `publishedAt`
- optional `assets`

### `data/refs.json`

Purpose:

- moving refs intentionally exposed to renderers
- development, maintenance, feature, and preview refs

Recommended fields:

- `provider`
- `componentSlug`
- `artifactKey`
- `kind`
- optional `namedRefKey`
- `ref`
- optional `displayVersion`
- optional `releaseLine`
- optional `maturity`
- optional `externalUrl`

### `data/content-index.json`

The content index should denormalize the most useful provider context for each
page so renderers can query page collections without joining multiple files.

Recommended provider-derived additions:

- `provider`
- optional `externalId`
- optional `versionKind`
- optional `versionLabel`
- optional `releaseLine`
- optional `supportStatus`
- optional `maturity`
- optional `candidateSequence`
- optional `voteStatus`

## Mapping by record kind

Recommended mapping behavior:

- `released`
  - emit entry in `data/releases.json`
  - merge authored exact-release publication state and withdrawal behavior when
    present
  - enrich `data/artifacts.json` latest release and line summaries
  - copy page-local release context into front matter for pages staged from that
    release
- `candidate`
  - emit entry in `data/candidates.json`
  - enrich `data/artifacts.json` latest candidate summary
  - copy page-local candidate context into front matter for candidate pages
- `namedRef`
  - emit entry in `data/refs.json`
  - carry the authored `namedRefKey` when the ref matches one
  - copy ref context into front matter for pages staged from that ref
- `lineHead`
  - emit entry in `data/refs.json`
  - enrich matching release-line summaries in `data/artifacts.json`
  - copy `lineHead` context into front matter when applicable
- `development`
  - emit entry in `data/refs.json`
  - mark artifact development context in `data/artifacts.json`
  - copy development ref context into front matter for development pages

## What should not be copied into front matter

To keep front matter compact, the pipeline should avoid embedding:

- full release inventories
- full candidate histories
- every downloadable asset for unrelated versions
- complete provider payloads
- large provider-specific passthrough payloads

Only the normalized subset of those inventories belongs in aggregate files. Raw
provider payloads and passthrough-only fields should stay out of the public
staged contract.

## Provider-specific passthrough data

When provider data includes extra fields that do not fit the normalized staged
contract, the pipeline should not copy them into public staged metadata in v1.

Recommended rule:

- normalize only the documented shared fields into `data/*.json`
- do not copy provider-specific passthrough payloads into page front matter
- do not expose private or API-only provider endpoints via public staged outputs

## Validation expectations

The pipeline should reject or warn on at least:

- provider-backed pages that refer to no matching normalized record
- multiple normalized records competing for the same staged page context
- provider records mapped to the wrong artifact or component
- provider-specific passthrough fields copied into public staged outputs
- large provider payloads copied wholesale into front matter

## Worked example

Given this provider record:

```yaml
- provider: atr
  kind: candidate
  componentSlug: spark
  artifactKey: runtime
  version: 4.1.0
  displayVersion: 4.1.0-rc2
  releaseLine: 4.x
  candidateSequence: 2
  voteStatus: open
```

The pipeline should typically emit:

- one entry in `data/candidates.json`
- an updated candidate summary in `data/artifacts.json`
- candidate/version context in front matter for pages staged from that candidate
- denormalized candidate fields in `data/content-index.json` for those pages