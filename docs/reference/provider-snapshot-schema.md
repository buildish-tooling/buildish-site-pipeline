---
title: "Provider snapshot schema"
description: "This document defines a normalized input schema for external release providers. It complements the flexible publication model by making the provider boundary concrete without hard-coding Apache Trusted Releases (ATR) or any other provider into the core pipeline model."
weight: 26
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

Intentional publication of named refs remains authored in the catalog or artifact
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
