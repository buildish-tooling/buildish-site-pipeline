---
title: "Incremental bookkeeping types"
description: "Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`."
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

Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Type index

- [AggregateDependencyEntryV1](#aggregatedependencyentryv1) — One coordinator-owned aggregate and the units that may change its payload.
- [AggregateDependencyMapV1](#aggregatedependencymapv1) — Shared-output dependency map for the current first-wave coordinator outputs.
- [OutputOwnershipClaimV1](#outputownershipclaimv1) — One exact published file or directory root together with its logical owner.
- [OutputOwnershipMapV1](#outputownershipmapv1) — Published ownership inventory used to prune retained stages safely.
- [PersistedUnitContributionsV1](#persistedunitcontributionsv1) — Stable per-unit page contribution manifests retained in the visible stage.
- [StagedPageContributionWire](#stagedpagecontributionwire) — Metadata emitted by one page-staging worker for later aggregation.
- [UnitContributionManifestWire](#unitcontributionmanifestwire) — Worker-emitted contribution fragment consumed by the coordinator.

<a id="aggregatedependencyentryv1"></a>
### AggregateDependencyEntryV1

One coordinator-owned aggregate and the units that may change its payload.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="aggregatedependencyentryv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Coordinator-owned aggregate file inside the visible stage. |
| <a id="aggregatedependencyentryv1-dependentunitids"></a>`dependentUnitIds` | tuple[str, ...] | no | Unit identifiers whose output can invalidate or change this aggregate file. |

#### Selected field examples

- `stageRelativePath`: Example: `"data/components.json"`

<a id="aggregatedependencymapv1"></a>
### AggregateDependencyMapV1

Shared-output dependency map for the current first-wave coordinator outputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/aggregate-dependencies.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="aggregatedependencymapv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | Schema version for the aggregate-dependency map. |
| <a id="aggregatedependencymapv1-entries"></a>`entries` | tuple[[AggregateDependencyEntryV1](#aggregatedependencyentryv1), ...] | no | Coordinator-owned aggregate files together with the units that may change them. |

#### Example: Aggregate dependency map that marks which units can invalidate one shared file.

```json
{
  "schemaVersion": 1,
  "entries": [
    {
      "stageRelativePath": "data/components.json",
      "dependentUnitIds": [
        "component:spark:runtime",
        "component:spark:site"
      ]
    }
  ]
}
```

<a id="outputownershipclaimv1"></a>
### OutputOwnershipClaimV1

One exact published file or directory root together with its logical owner.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="outputownershipclaimv1-ownerid"></a>`ownerId` | str | yes | Logical owner identifier for the output, such as a unit owner id or the coordinator. |
| <a id="outputownershipclaimv1-unitid"></a>`unitId` | str | no | Unit identifier when the owning output belongs to one concrete staging unit. |
| <a id="outputownershipclaimv1-pathkind"></a>`pathKind` | Literal['directory', 'file'] | yes | Whether the owned stage-relative path refers to one exact file or one directory root. |
| <a id="outputownershipclaimv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](../pipeline-shared-types-reference/#stagerelativepath) | yes | Owned path inside the visible stage. |

#### Selected field examples

- `ownerId`: Example: `"coordinator"`
- `unitId`: Example: `"component:spark:runtime"`
- `stageRelativePath`: Example: `"content/spark"`

<a id="outputownershipmapv1"></a>
### OutputOwnershipMapV1

Published ownership inventory used to prune retained stages safely.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/output-ownership.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="outputownershipmapv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | Schema version for the output-ownership map. |
| <a id="outputownershipmapv1-claims"></a>`claims` | tuple[[OutputOwnershipClaimV1](#outputownershipclaimv1), ...] | no | Ownership claims for every retained stage file or directory root. |

#### Example: Ownership claims for one unit directory and one coordinator aggregate file.

```json
{
  "schemaVersion": 1,
  "claims": [
    {
      "ownerId": "artifact:spark/runtime",
      "unitId": "component:spark:runtime",
      "pathKind": "directory",
      "stageRelativePath": "content/spark/4.0.0"
    },
    {
      "ownerId": "coordinator",
      "pathKind": "file",
      "stageRelativePath": "data/components.json"
    }
  ]
}
```

<a id="persistedunitcontributionsv1"></a>
### PersistedUnitContributionsV1

Stable per-unit page contribution manifests retained in the visible stage.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/unit-contributions.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="persistedunitcontributionsv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | Schema version for the persisted unit-contribution manifest file. |
| <a id="persistedunitcontributionsv1-units"></a>`units` | tuple[[UnitContributionManifestWire](#unitcontributionmanifestwire), ...] | no | Worker contribution manifests retained for every staged unit that currently owns visible output. |

#### Example: Retained per-unit contribution map with one staged page.

```json
{
  "schemaVersion": 1,
  "units": [
    {
      "unitId": "component:spark:runtime",
      "pages": [
        {
          "stageRelativePath": "content/spark/4.0.0/docs/getting-started/index.md",
          "componentSlug": "spark",
          "artifactKey": "runtime",
          "section": "documentation",
          "pageKind": "docsPage",
          "publicPath": "/spark/4.0.0/docs/getting-started/",
          "componentPath": "/spark/",
          "originKey": "archive",
          "versionKind": "released",
          "version": "4.0.0",
          "defaultLocale": false,
          "title": "Getting Started",
          "sourcePath": "docs/runtime/getting-started.md"
        }
      ]
    }
  ]
}
```

<a id="stagedpagecontributionwire"></a>
### StagedPageContributionWire

Metadata emitted by one page-staging worker for later aggregation.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedpagecontributionwire-stagerelativepath"></a>`stageRelativePath` | str | yes | Stage-relative file path of the staged page contribution. |
| <a id="stagedpagecontributionwire-componentslug"></a>`componentSlug` | str | yes | Owning component slug for the staged page. |
| <a id="stagedpagecontributionwire-artifactkey"></a>`artifactKey` | str | no | Owning artifact key when the page belongs to a specific artifact. |
| <a id="stagedpagecontributionwire-section"></a>`section` | str | yes | Higher-level section label for the staged page. |
| <a id="stagedpagecontributionwire-pagekind"></a>`pageKind` | str | yes | Short page-kind label for the staged page. |
| <a id="stagedpagecontributionwire-publicpath"></a>`publicPath` | str | yes | Published public path for the staged page. |
| <a id="stagedpagecontributionwire-publicurl"></a>`publicUrl` | str | no | Canonical absolute URL for the staged page, if known. |
| <a id="stagedpagecontributionwire-componentpath"></a>`componentPath` | str | yes | Public root path for the owning component. |
| <a id="stagedpagecontributionwire-componenturl"></a>`componentUrl` | str | no | Absolute URL root for the owning component, if known. |
| <a id="stagedpagecontributionwire-originkey"></a>`originKey` | str | yes | Origin key selected for the staged page. |
| <a id="stagedpagecontributionwire-versioncontext"></a>`versionContext` | dict[str, object] | no | Serialized version-context payload associated with the staged page. |
| <a id="stagedpagecontributionwire-versionkind"></a>`versionKind` | str | no | Version-record kind associated with the staged page, if present. |
| <a id="stagedpagecontributionwire-versionref"></a>`versionRef` | str | no | Source-control ref associated with the staged page, if present. |
| <a id="stagedpagecontributionwire-version"></a>`version` | str | no | Exact version string associated with the staged page, if present. |
| <a id="stagedpagecontributionwire-locale"></a>`locale` | str | no | Locale key for the staged page when localization is enabled. |
| <a id="stagedpagecontributionwire-defaultlocale"></a>`defaultLocale` | bool | no | Whether the staged page represents the default locale within its translation group. |
| <a id="stagedpagecontributionwire-translationkey"></a>`translationKey` | str | no | Shared key that ties translated sibling pages together. |
| <a id="stagedpagecontributionwire-title"></a>`title` | str | no | Primary page title extracted during staging. |
| <a id="stagedpagecontributionwire-linktitle"></a>`linkTitle` | str | no | Shorter link title extracted during staging, if present. |
| <a id="stagedpagecontributionwire-description"></a>`description` | str | no | Primary page description extracted or derived during staging, if present. |
| <a id="stagedpagecontributionwire-derivedtitle"></a>`derivedTitle` | str | no | Body-derived page title inferred from authored content during staging, if present. |
| <a id="stagedpagecontributionwire-deriveddescription"></a>`derivedDescription` | str | no | Body-derived page description inferred from authored content during staging, if present. |
| <a id="stagedpagecontributionwire-sourcepath"></a>`sourcePath` | str | yes | Source file path that produced the staged page. |
| <a id="stagedpagecontributionwire-canonicalurl"></a>`canonicalUrl` | str | no | Explicit canonical URL for the page when it should differ from `publicUrl`. |

#### Selected field examples

- `stageRelativePath`: Example: `"content/spark/4.0.0/docs/getting-started/index.md"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `section`: Example: `"documentation"`
- `pageKind`: Example: `"docsPage"`
- `publicPath`: Example: `"/spark/4.0.0/docs/getting-started/"`
- `componentPath`: Example: `"/spark/"`
- `originKey`: Example: `"archive"`
- `versionKind`: Example: `"release"`
- `versionRef`: Example: `"refs/tags/v4.0.0"`
- `version`: Example: `"4.0.0"`
- `locale`: Example: `"en"`
- `translationKey`: Example: `"spark-overview"`
- `title`: Example: `"Getting Started"`
- `linkTitle`: Example: `"Start"`
- `derivedTitle`: Example: `"Getting Started"`
- `sourcePath`: Example: `"docs/runtime/getting-started.md"`

<a id="unitcontributionmanifestwire"></a>
### UnitContributionManifestWire

Worker-emitted contribution fragment consumed by the coordinator.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="unitcontributionmanifestwire-unitid"></a>`unitId` | str | yes | Worker unit identifier that owns this contribution manifest. |
| <a id="unitcontributionmanifestwire-pages"></a>`pages` | tuple[[StagedPageContributionWire](#stagedpagecontributionwire), ...] | no | Staged page contributions emitted by the worker for later aggregation. |

#### Selected field examples

- `unitId`: Example: `"component:spark:runtime"`

