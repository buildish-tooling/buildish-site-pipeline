---
title: "Provider snapshot schema"
description: "This document defines a normalized input schema for external release providers. It complements the flexible publication model by making the provider boundary concrete without hard-coding Apache Trusted Releases (ATR) or any other provider into the core pipeline model."
weight: 26
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

## Goals

- keep the provider contract small and versioned,
- support ATR, Git-hosting release APIs, and future providers,
- preserve provider-specific detail without polluting the core contract,
- let renderers rely on staged metadata rather than direct provider calls, and
- keep authored site metadata authoritative for routing and identity.

## Top-level snapshot shape

Recommended shape:

- `schemaVersion`
- `providers[]`
- `records[]`

Recommended `providers[]` fields:

- `key`
- `type`
- optional `displayName`
- optional public `baseUrl`
- `fetchedAt`

## Component-owned artifact decisions

`site/component.yaml` defines artifact identities, static streams, relative content
roots, and reusable support defaults. Snapshot `artifacts[]` entries are scoped by
`componentSlug` and `artifactKey` and own optional `latestStable`, `releaseLines[]`,
and curated exact `releases[]` lifecycle facts. They require no provider descriptor
or synthetic provider record. Records may enrich these decisions with upstream facts.

Each release line has an explicit `latest` released target and optional `parent`.
The target must have a canonical primary `releaseLine` and belong to the designated
line or a descendant. Ancestors derive from the parent graph; supplied record
`releaseLineAncestors` must match that ordered chain. Several lines may designate
the same release, which is published once. Neither version sorting nor publication
pins change these component decisions. A candidate with the same version is a
different context and cannot satisfy a released target.

A configured catalog `providerSnapshot` binding reserves all version facts for that
component, even when its file is optional and missing or contains no records. An
aggregate inventory must not claim that component through either an artifact section
or a record, including unrelated versions or kinds. It may still contain inventory
for unbound components and shared provider descriptors.

Artifact `latestStable` remains visible independently of publication selection.
The emitted component scalar is derived only for a component defining exactly one
artifact; zero or multiple artifacts omit it. Missing optional inventory means an
unknown recommendation, with no static metadata or catalog fallback.

## Minimal normalized `records[]` schema

Required fields on every record:

- `provider`
- `kind`
- `componentSlug`
- `artifactKey`

Each record should also provide at least one stable locator:

- `externalId`, or
- `version`, or
- `tag`, or
- `ref`

Recommended shared optional fields:

- `sourceKey`
- `externalUrl`
- `displayVersion`
- `commitSha`
- `releaseLine`
- `releaseLineAncestors`
- `supportStatus`
- `maturity`
- `candidateSequence`
- `voteStatus`
- `createdAt`
- `publishedAt`
- `updatedAt`
- `urls`
- `assets`

## Record kinds

Recommended shared `kind` values:

- `development`
- `namedRef`
- `lineHead`
- `candidate`
- `released`

Kind-specific expectations:

- `development`: usually carries `ref`
- `namedRef`: should carry `ref`
- `lineHead`: should carry `releaseLine` and usually `ref`
- `candidate`: should normally carry `version`; `candidateSequence` is recommended
- `released`: should normally carry `version` and usually `tag`

The pipeline should treat `kind` as the primary normalized lifecycle category.
Fields such as `maturity`, `supportStatus`, and `voteStatus` add detail but do
not replace `kind`.

## Merge precedence

The provider snapshot is one input into the build, not the whole truth.

Recommended precedence rules:

1. authored site/catalog/component metadata owns:
   - component identity
   - artifact identity
   - publication routing
   - grouping and navigation defaults
   - support-status vocabularies
2. provider snapshots own externally observed release state:
   - discovered releases
   - candidates and vote state
   - development refs and release-line heads
   - provider-observed details for authored named refs when they can be matched
   - provider URLs and timestamps
   - downloadable assets
3. explicit local override files, if introduced later, should override provider
   data in a narrow and auditable way

Provider data must not silently redefine consumer-owned URLs or artifact
identity.

Planning should reject snapshots whose records point at component/artifact
identities that do not exist in the resolved site config. It should also reject
snapshots that exceed the planning ceilings of 50,000 normalized records or 16
MiB of encoded snapshot input.

Intentional publication of named refs remains selected in the catalog; static ref definitions belong to component metadata. The
metadata. Provider data may enrich those refs, but it does not define which named
refs exist as public version contexts.

## Minimal optional `assets[]` schema

`assets[]` should remain lightweight and nested under a release or candidate
record.

Required fields:

- `name`
- `url`

Recommended optional fields:

- `kind`
- `mediaType`
- `size`
- `checksums`
- `signatureUrl`
- `sbomUrl`
- `provenanceUrl`

Useful advisory `kind` values include:

- `archive`
- `signature`
- `checksum`
- `sbom`
- `provenance`
- `container-image`
- `package`

`checksums` should prefer a simple algorithm-keyed map such as `sha512` or
`sha256`.

## Example: ATR-style snapshot

```yaml
schemaVersion: 1
providers:
  - key: atr
    type: atr
    displayName: Apache Trusted Releases
    baseUrl: https://release-test.apache.org
    fetchedAt: 2026-04-02T12:00:00Z
records:
  - provider: atr
    kind: candidate
    componentSlug: spark
    artifactKey: runtime
    externalId: atr:candidate:spark-runtime:4.1.0:2
    externalUrl: https://release-test.apache.org/candidates/spark-runtime/4.1.0/2
    version: 4.1.0
    displayVersion: 4.1.0-rc2
    maturity: rc
    candidateSequence: 2
    voteStatus: open
    releaseLine: 4.x
  - provider: atr
    kind: released
    componentSlug: spark
    artifactKey: runtime
    externalId: atr:release:spark-runtime:4.0.0
    version: 4.0.0
    tag: v4.0.0
```

## Example: GitHub-release-style snapshot

```yaml
schemaVersion: 1
providers:
  - key: github
    type: github-releases
    displayName: GitHub Releases
    baseUrl: https://github.com
    fetchedAt: 2026-04-02T12:05:00Z
records:
  - provider: github
    kind: released
    componentSlug: spark
    artifactKey: runtime
    externalId: github:release:12345
    externalUrl: https://github.com/apache/spark/releases/tag/v4.0.0
    version: 4.0.0
    tag: v4.0.0
    publishedAt: 2026-03-10T08:00:00Z
  - provider: github
    kind: candidate
    componentSlug: spark
    artifactKey: runtime
    externalId: github:release:12346
    externalUrl: https://github.com/apache/spark/releases/tag/v4.1.0-rc1
    version: 4.1.0
    displayVersion: 4.1.0-rc1
    maturity: rc
    publishedAt: 2026-03-15T10:00:00Z
```

## Validation expectations

The pipeline should reject at least:

- unknown `provider` keys,
- unknown `componentSlug` or `artifactKey` references,
- duplicate records for the same `(provider, externalId)` pair when `externalId`
  exists,
- records that provide none of `externalId`, `version`, `tag`, or `ref`, and
- records whose `kind` is outside the shared normalized vocabulary, and
- unknown extra fields outside the documented provider, record, and asset
  schemas.

## Component-owned inventory files

An aggregate snapshot beside the catalog remains supported. A component may also
bind its own normalized file in the catalog:

```yaml
components:
  - slug: release-tooling
    content:
      source: release-tooling
    providerSnapshot:
      source: release-tooling
      path: docs/releases/provider-snapshot.json
      requirement: publication
```

The source must be an existing named catalog source. The path is relative to that
source checkout, never to the process working directory. It follows the ordinary
containment rules. Records must name the owning component and one of its catalog
artifacts; an explicit record sourceKey must match that artifact's source.

`requirement` accepts `publication` (the default), `required`, and `optional`.
Commands default to `--profile local`; publication automation must explicitly use
`--profile publication`. A publication requirement allows absence locally and
requires the file for publication. A required file must exist in both profiles;
an optional file may be absent in either. An always-optional file can intentionally
produce incomplete publication. Profiles are not inferred from CI environment
variables or branch names. Present invalid or unreadable files are always errors.

Pipeline composes these inputs internally. Provider descriptors sharing a key must
agree on type, display name, and base URL. Their refresh times may differ: per-file
provenance retains the actual times; a combined descriptor uses the latest time.
Duplicate `(provider, externalId)` identities across files fail with both sources
identified. Multiple records for a selected context retain ambiguity diagnostics.
The 16 MiB input and 50,000-record ceilings also apply to the combined inventory.

When absence is allowed, unavailable original release-doc trees belonging to that
component may be omitted locally. Explicit selection stays visible in report
context dispositions; an absent inventory cannot enumerate unknown versions for
`allKnown` or `latestN`. Existing local trees remain usable without provider data.
A present snapshot, or a present aggregate record for a selected release, still
requires that release's original docs unless publication state excludes them.
An empty present snapshot is not an absent checkout. Unverified explicit selections
receive a notice during allowed absence; strict identity checks resume once the
inventory is present. Other components and non-release contexts are unaffected.

A `versioned-docs` branch is one consumer-owned materialization strategy. Pipeline
neither checks out that branch nor fetches a provider API. Consumers must acquire
inventory and docs consistently and select the publication profile in their full
publication build. Configured provider files and Git bookkeeping are not published
as ordinary documentation assets, including beneath a development docs root.
