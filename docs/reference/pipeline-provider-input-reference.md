---
title: "Provider input types"
description: "Normalized provider snapshot contracts consumed by the pipeline."
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

Normalized provider snapshot contracts consumed by the pipeline.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Type index

- [ProviderAsset](#providerasset) — Downloadable asset attached to one provider release or candidate record.
- [ProviderDescriptor](#providerdescriptor) — Metadata about one provider that contributed records to the snapshot.
- [ProviderRecord](#providerrecord) — Normalized provider fact about one release, candidate, or ref context.
- [ProviderSnapshotDocumentV1](#providersnapshotdocumentv1) — Provider-derived normalized snapshot from ``site/provider-snapshot.json``.

<a id="providerasset"></a>
### ProviderAsset

Downloadable asset attached to one provider release or candidate record.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerasset-name"></a>`name` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Filename or display label of the downloadable asset. |
| <a id="providerasset-url"></a>`url` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Canonical download URL for the asset. |
| <a id="providerasset-kind"></a>`kind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short asset kind label, for example `binary`, `source`, `signature`, or `sbom`. |
| <a id="providerasset-mediatype"></a>`mediaType` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Declared media type for the asset payload when the provider exposes it. |
| <a id="providerasset-size"></a>`size` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | no | Asset size in bytes when the provider exposes it. |
| <a id="providerasset-checksums"></a>`checksums` | dict[[Identifier](../pipeline-shared-types-reference/#identifier), [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Checksum values keyed by algorithm name, such as `sha512` or `sha256`. |
| <a id="providerasset-signatureurl"></a>`signatureUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | URL of the detached signature file, if available. |
| <a id="providerasset-sbomurl"></a>`sbomUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | URL of the asset's software bill of materials, if available. |
| <a id="providerasset-provenanceurl"></a>`provenanceUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | URL of provenance or attestation metadata associated with this asset, if available. |

#### Selected field examples

- `name`: Example: `"spark-4.0.0-bin.tgz"`
- `url`: Example: `"https://downloads.example.org/spark-4.0.0-bin.tgz"`
- `kind`: Example: `"binary"`
- `mediaType`: Example: `"application/gzip"`
- `size`: Example: `125004321`

<a id="providerdescriptor"></a>
### ProviderDescriptor

Metadata about one provider that contributed records to the snapshot.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerdescriptor-key"></a>`key` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | yes | Stable provider identifier referenced by every record emitted from this provider. |
| <a id="providerdescriptor-type"></a>`type` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Provider implementation type, such as `github`, `git`, or another fetcher-specific backend name. |
| <a id="providerdescriptor-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable provider label shown in diagnostics or rendered metadata. |
| <a id="providerdescriptor-baseurl"></a>`baseUrl` | [ProviderBaseUrl](../pipeline-shared-types-reference/#providerbaseurl) | no | Base URL for the provider service when records can link back to a human-browsable origin. |
| <a id="providerdescriptor-fetchedat"></a>`fetchedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | yes | Timestamp when this provider snapshot section was fetched or refreshed. |

#### Selected field examples

- `key`: Example: `"github-releases"`
- `type`: Example: `"github"`
- `displayName`: Example: `"GitHub Releases"`
- `baseUrl`: Example: `"https://github.com/apache"`
- `fetchedAt`: Example: `"2026-04-03T18:00:00Z"`

<a id="providerrecord"></a>
### ProviderRecord

Normalized provider fact about one release, candidate, or ref context.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerrecord-provider"></a>`provider` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | yes | Provider key that identifies which fetched provider emitted this record. |
| <a id="providerrecord-kind"></a>`kind` | [RecordKind](../pipeline-shared-types-reference/#recordkind) | yes | Record kind, such as exact release, release candidate, development ref, line head, or named ref. |
| <a id="providerrecord-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Component slug that this provider record belongs to. |
| <a id="providerrecord-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Artifact key that this provider record belongs to. |
| <a id="providerrecord-sourcekey"></a>`sourceKey` | [SourceKey](../pipeline-shared-types-reference/#sourcekey) | no | Optional source binding key when the provider record came from one named catalog source. |
| <a id="providerrecord-externalid"></a>`externalId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Provider-specific stable identifier used to deduplicate and revisit the same upstream record. |
| <a id="providerrecord-externalurl"></a>`externalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Human-browsable upstream URL for the release, tag, or ref record. |
| <a id="providerrecord-version"></a>`version` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Exact version string for release and candidate records when the provider exposes one. |
| <a id="providerrecord-displayversion"></a>`displayVersion` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable version label when the raw version string needs a friendlier presentation. |
| <a id="providerrecord-tag"></a>`tag` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Exact provider tag associated with this record when tags are available. |
| <a id="providerrecord-ref"></a>`ref` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Exact source-control ref associated with this record, especially for development, line-head, or named-ref contexts. |
| <a id="providerrecord-commitsha"></a>`commitSha` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Resolved commit SHA for the record when the provider exposes it. |
| <a id="providerrecord-namedrefkey"></a>`namedRefKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Catalog-authored named-ref key that this provider record enriches when the record represents a named ref. |
| <a id="providerrecord-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key that groups this record with related versions such as `4.0`. |
| <a id="providerrecord-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Ancestor release-line keys, ordered from nearest to farthest, used when lineage matters to selection or rendering. |
| <a id="providerrecord-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label associated with this record. |
| <a id="providerrecord-publicationstate"></a>`publicationState` | [PublicationState](../pipeline-shared-types-reference/#publicationstate) | no | Publication state for the record, such as published, withdrawn, or tombstoned. |
| <a id="providerrecord-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Maturity label such as preview, beta, or stable that readers can use to judge readiness. |
| <a id="providerrecord-candidatesequence"></a>`candidateSequence` | [NonNegativeInteger](../pipeline-shared-types-reference/#nonnegativeinteger) | no | Numeric ordering hint for release candidates, usually the `rc` sequence number. |
| <a id="providerrecord-votestatus"></a>`voteStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Vote status label for a candidate release when the provider exposes release-vote state. |
| <a id="providerrecord-createdat"></a>`createdAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp when the upstream record was first created. |
| <a id="providerrecord-publishedat"></a>`publishedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp when the upstream record became publicly available. |
| <a id="providerrecord-updatedat"></a>`updatedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp of the most recent upstream update observed for this record. |
| <a id="providerrecord-urls"></a>`urls` | dict[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring), [UrlString](../pipeline-shared-types-reference/#urlstring)] | no | Additional named URLs related to the record, such as notes, signatures, vote threads, or changelogs. |
| <a id="providerrecord-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] | no | Downloadable assets attached to the record, including checksums and related provenance links when available. |

#### Selected field examples

- `provider`: Example: `"github-releases"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `sourceKey`: Example: `"apache-spark"`
- `externalId`: Example: `"github:release:runtime-4.0.0"`
- `version`: Example: `"4.0.0"`
- `displayVersion`: Example: `"4.0.0 GA"`
- `tag`: Example: `"v4.0.0"`
- `ref`: Example: `"refs/heads/main"`
- `commitSha`: Example: `"6f0fd1f7b2c4a6d8e9f00123456789abcdef0123"`
- `namedRefKey`: Example: `"preview"`
- `releaseLine`: Example: `"4.0"`
- `releaseLineAncestors`: Example: `["4.x","stable"]`
- `supportStatus`: Example: `"supported"`
- `maturity`: Example: `"stable"`
- `candidateSequence`: Example: `1`
- `voteStatus`: Example: `"passed"`

<a id="providersnapshotdocumentv1"></a>
### ProviderSnapshotDocumentV1

Provider-derived normalized snapshot from `site/provider-snapshot.json`.

- category: `provider`
- ownership: `provider-derived`
- file contract: `site/provider-snapshot.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providersnapshotdocumentv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the provider snapshot document. |
| <a id="providersnapshotdocumentv1-providers"></a>`providers` | list[[ProviderDescriptor](#providerdescriptor)] | yes | Provider descriptors for every provider that contributed records to this snapshot. |
| <a id="providersnapshotdocumentv1-records"></a>`records` | list[[ProviderRecord](#providerrecord)] | yes | Normalized provider records for releases, candidates, tags, refs, and related downloadable assets. |

#### Example: Provider snapshot with one released record and one downloadable asset.

```json
{
  "schemaVersion": 1,
  "providers": [
    {
      "key": "github-releases",
      "type": "github",
      "displayName": "GitHub Releases",
      "baseUrl": "https://github.com/apache/spark",
      "fetchedAt": "2026-04-03T18:00:00Z"
    }
  ],
  "records": [
    {
      "provider": "github-releases",
      "kind": "released",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "externalId": "spark-4.0.0",
      "externalUrl": "https://github.com/apache/spark/releases/tag/v4.0.0",
      "version": "4.0.0",
      "publishedAt": "2026-04-03T18:00:00Z",
      "assets": [
        {
          "name": "spark-4.0.0-src.tgz",
          "url": "https://downloads.apache.org/spark/spark-4.0.0-src.tgz",
          "checksums": {
            "sha256": "abc123"
          }
        }
      ]
    }
  ]
}
```

