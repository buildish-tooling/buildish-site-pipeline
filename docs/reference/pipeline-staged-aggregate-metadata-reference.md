---
title: "Staged aggregate metadata types"
description: "Public aggregate JSON contracts emitted under `data/`."
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

Public aggregate JSON contracts emitted under `data/`.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Type index

- [ArtifactsDataEntry](#artifactsdataentry) — Entry in ``data/artifacts.json``.
- [CandidateAggregateEntry](#candidateaggregateentry) — Entry in ``data/candidates.json``.
- [CompatibilityAggregateEntry](#compatibilityaggregateentry) — Entry in ``data/compatibility.json``.
- [ComponentsDataEntry](#componentsdataentry) — Entry in ``data/components.json``.
- [ContentIndexEntry](#contentindexentry) — Entry in ``data/content-index.json``.
- [LatestCandidateSummary](#latestcandidatesummary) — Compact latest-candidate summary embedded in artifact aggregates.
- [LatestReleaseSummary](#latestreleasesummary) — Compact latest-release summary embedded in artifact aggregates.
- [MountAggregateEntry](#mountaggregateentry) — Entry in ``data/mounts.json``.
- [ProvidersDataEntry](#providersdataentry) — Entry in ``data/providers.json``.
- [RedirectAggregateEntry](#redirectaggregateentry) — Entry in ``data/redirects.json``.
- [RefAggregateEntry](#refaggregateentry) — Entry in ``data/refs.json``.
- [ReleaseAggregateEntry](#releaseaggregateentry) — Entry in ``data/releases.json``.
- [RouteAggregateEntry](#routeaggregateentry) — Entry in ``data/routes.json``.
- [TranslationSetAggregateEntry](#translationsetaggregateentry) — Entry in ``data/translations.json``.

<a id="artifactsdataentry"></a>
### ArtifactsDataEntry

Entry in `data/artifacts.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactsdataentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the artifact. |
| <a id="artifactsdataentry-key"></a>`key` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Stable artifact key used by routes, aggregates, and typed references. |
| <a id="artifactsdataentry-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable artifact label shown in navigation and metadata. |
| <a id="artifactsdataentry-sourcekey"></a>`sourceKey` | [SourceKey](../pipeline-shared-types-reference/#sourcekey) | no | Named source binding that owns the artifact's docs and assets. |
| <a id="artifactsdataentry-docsroot"></a>`docsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Repository-relative docs root for the artifact when it differs from the component default. |
| <a id="artifactsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](../pipeline-shared-types-reference/#providerkey)] | no | Provider keys that contributed version metadata for this artifact. |
| <a id="artifactsdataentry-versioning"></a>`versioning` | [ArtifactVersioningConfig](../pipeline-authored-input-reference/#artifactversioningconfig) | no | Version-discovery rules that explain how development refs, tags, and named refs are derived for the artifact. |
| <a id="artifactsdataentry-lateststable"></a>`latestStable` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Most recent stable version recommended for readers. |
| <a id="artifactsdataentry-latestrelease"></a>`latestRelease` | [LatestReleaseSummary](#latestreleasesummary) | no | Compact summary of the latest known release for the artifact. |
| <a id="artifactsdataentry-latestcandidate"></a>`latestCandidate` | [LatestCandidateSummary](#latestcandidatesummary) | no | Compact summary of the latest known release candidate for the artifact. |
| <a id="artifactsdataentry-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](../pipeline-staged-front-matter-reference/#releaselinesummary)] | no | Release-line summaries associated with the artifact. |
| <a id="artifactsdataentry-namedrefs"></a>`namedRefs` | list[[RefAggregateEntry](#refaggregateentry)] | no | Published development, line-head, or named-ref contexts associated with the artifact. |
| <a id="artifactsdataentry-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring), [SupportStatusDefinition](../pipeline-authored-input-reference/#supportstatusdefinition)] | no | Reusable support-status definitions that release lines and releases for this artifact can refer to by key. |
| <a id="artifactsdataentry-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Canonical URL for the support policy document associated with this artifact. |

#### Selected field examples

- `componentSlug`: Example: `"spark"`
- `key`: Example: `"runtime"`
- `displayName`: Example: `"Runtime"`
- `sourceKey`: Example: `"apache-spark"`
- `docsRoot`: Example: `"docs/runtime"`
- `providerKeys`: Example: `["github-releases"]`
- `latestStable`: Example: `"4.0.1"`

<a id="candidateaggregateentry"></a>
### CandidateAggregateEntry

Entry in `data/candidates.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="candidateaggregateentry-provider"></a>`provider` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | no | Provider key for the upstream system that supplied this candidate record. |
| <a id="candidateaggregateentry-externalid"></a>`externalId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Provider-specific stable identifier for the upstream candidate record. |
| <a id="candidateaggregateentry-externalurl"></a>`externalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Human-browsable upstream URL for the candidate record. |
| <a id="candidateaggregateentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the candidate. |
| <a id="candidateaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Owning artifact key for the candidate. |
| <a id="candidateaggregateentry-version"></a>`version` | [VersionString](../pipeline-shared-types-reference/#versionstring) | yes | Candidate version string represented by this aggregate entry. |
| <a id="candidateaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable candidate label when it should differ from the raw version string. |
| <a id="candidateaggregateentry-candidatesequence"></a>`candidateSequence` | int | no | Numeric ordering hint for the candidate, usually the `rc` sequence number. |
| <a id="candidateaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key that the candidate belongs to, if known. |
| <a id="candidateaggregateentry-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Maturity label associated with the candidate. |
| <a id="candidateaggregateentry-votestatus"></a>`voteStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Vote-status label for the candidate, if known. |
| <a id="candidateaggregateentry-createdat"></a>`createdAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp when the candidate record was first created. |
| <a id="candidateaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp when the candidate became publicly visible. |
| <a id="candidateaggregateentry-assets"></a>`assets` | list[[ProviderAsset](../pipeline-provider-input-reference/#providerasset)] | no | Downloadable assets attached to the candidate. |

#### Selected field examples

- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `version`: Example: `"4.1.0-rc1"`
- `candidateSequence`: Example: `1`
- `releaseLine`: Example: `"4.1"`
- `maturity`: Example: `"preview"`
- `voteStatus`: Example: `"passed"`

<a id="compatibilityaggregateentry"></a>
### CompatibilityAggregateEntry

Entry in `data/compatibility.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="compatibilityaggregateentry-subjectid"></a>`subjectId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Typed reference or aggregate identifier for the subject of the compatibility statement. |
| <a id="compatibilityaggregateentry-targetid"></a>`targetId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Typed reference or aggregate identifier for the target of the compatibility statement. |
| <a id="compatibilityaggregateentry-relation"></a>`relation` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Relationship label that names the compatibility statement. |
| <a id="compatibilityaggregateentry-scope"></a>`scope` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional scope label that narrows the compatibility statement. |
| <a id="compatibilityaggregateentry-confidence"></a>`confidence` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional confidence label that explains how strong the supporting evidence is. |
| <a id="compatibilityaggregateentry-notes"></a>`notes` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Additional human-readable explanation, caveats, or migration advice for the compatibility statement. |
| <a id="compatibilityaggregateentry-evidence"></a>`evidence` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Named evidence pointers or short evidence labels that support the compatibility statement. |

#### Selected field examples

- `subjectId`: Example: `"artifact:spark/runtime"`
- `targetId`: Example: `"artifact:spark/operator"`
- `relation`: Example: `"testedWith"`
- `scope`: Example: `"kubernetes"`
- `confidence`: Example: `"verified"`

<a id="componentsdataentry"></a>
### ComponentsDataEntry

Entry in `data/components.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentsdataentry-slug"></a>`slug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Stable component slug used by routes, aggregates, and typed references. |
| <a id="componentsdataentry-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable component name shown in navigation, listings, and generated metadata. |
| <a id="componentsdataentry-lateststable"></a>`latestStable` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Most recent stable version recommended for the component as a whole when one shared release line is enough. |
| <a id="componentsdataentry-weight"></a>`weight` | int | no | Optional ordering hint copied from the authored catalog for consumer-rendered component lists. |
| <a id="componentsdataentry-group"></a>`group` | [Identifier](../pipeline-shared-types-reference/#identifier) | no | Optional group key copied from the authored catalog to support grouped rendering or filtering. |
| <a id="componentsdataentry-originkey"></a>`originKey` | [OriginKey](../pipeline-shared-types-reference/#originkey) | yes | Origin key selected for this component's primary published route set. |
| <a id="componentsdataentry-publication"></a>`publication` | [ResolvedPublication](../pipeline-staged-front-matter-reference/#resolvedpublication) | yes | Resolved publication roots and URLs for the component. |
| <a id="componentsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](../pipeline-shared-types-reference/#providerkey)] | no | Provider keys that contributed version metadata for this component's artifacts. |
| <a id="componentsdataentry-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](../pipeline-staged-front-matter-reference/#artifactfrontmattersummary)] | no | Compact artifact summaries used by component listings and page chrome. |

#### Selected field examples

- `slug`: Example: `"spark"`
- `displayName`: Example: `"Apache Spark"`
- `latestStable`: Example: `"4.0.1"`
- `group`: Example: `"data-platform"`
- `originKey`: Example: `"archive"`
- `providerKeys`: Example: `["github-releases"]`

<a id="contentindexentry"></a>
### ContentIndexEntry

Entry in `data/content-index.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="contentindexentry-id"></a>`id` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Stable identifier for the indexed page entry. |
| <a id="contentindexentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the indexed page. |
| <a id="contentindexentry-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | no | Owning artifact key when the page belongs to a specific artifact. |
| <a id="contentindexentry-pagekind"></a>`pageKind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Short page-kind label used for filtering and presentation. |
| <a id="contentindexentry-section"></a>`section` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Higher-level section label used for navigation or filtering. |
| <a id="contentindexentry-originkey"></a>`originKey` | [OriginKey](../pipeline-shared-types-reference/#originkey) | yes | Origin key that this indexed page belongs to. |
| <a id="contentindexentry-path"></a>`path` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Published public path for the page. |
| <a id="contentindexentry-url"></a>`url` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Canonical absolute URL for the page. |
| <a id="contentindexentry-canonicalurl"></a>`canonicalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Explicit canonical URL when it should differ from `url`. |
| <a id="contentindexentry-title"></a>`title` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Primary page title shown to readers. |
| <a id="contentindexentry-linktitle"></a>`linkTitle` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Shorter title variant used in navigation or link lists. |
| <a id="contentindexentry-description"></a>`description` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Longer page description intended for metadata or search snippets. |
| <a id="contentindexentry-summary"></a>`summary` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short summary used for listings, cards, or lightweight search results. |
| <a id="contentindexentry-weight"></a>`weight` | int | no | Optional ordering hint used by renderers for listings or navigation. |
| <a id="contentindexentry-parentid"></a>`parentId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Identifier of the parent indexed page when the page belongs to a hierarchy. |
| <a id="contentindexentry-ancestorids"></a>`ancestorIds` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Ancestor page identifiers ordered from nearest to farthest. |
| <a id="contentindexentry-source"></a>`source` | [PageSourceProvenance](../pipeline-staged-front-matter-reference/#pagesourceprovenance) | no | Repository-neutral provenance for the authored source file that produced this indexed page. |
| <a id="contentindexentry-versionkind"></a>`versionKind` | [RecordKind](../pipeline-shared-types-reference/#recordkind) | no | Version-context kind attached when the page belongs to a versioned route set. |
| <a id="contentindexentry-versionlabel"></a>`versionLabel` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable version label attached to the page, if present. |
| <a id="contentindexentry-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key attached to the page, if present. |
| <a id="contentindexentry-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label attached to the page's version context. |
| <a id="contentindexentry-publicationstate"></a>`publicationState` | [PublicationState](../pipeline-shared-types-reference/#publicationstate) | no | Publication-state label attached to the page's version context. |
| <a id="contentindexentry-locale"></a>`locale` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Locale key for the page when the page participates in localization. |
| <a id="contentindexentry-defaultlocale"></a>`defaultLocale` | bool | no | Whether the page represents the default locale within its translation group. |
| <a id="contentindexentry-translationkey"></a>`translationKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Shared key that ties translated sibling pages together. |
| <a id="contentindexentry-provider"></a>`provider` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | no | Provider key for the upstream record that informed the page's version metadata. |
| <a id="contentindexentry-externalid"></a>`externalId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Provider-specific stable identifier for the upstream record that informed the page. |
| <a id="contentindexentry-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Maturity label such as preview, beta, or stable. |
| <a id="contentindexentry-candidatesequence"></a>`candidateSequence` | int | no | Release-candidate sequence number when the page belongs to a candidate context. |
| <a id="contentindexentry-votestatus"></a>`voteStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Vote-status label when the page belongs to a candidate context. |

#### Selected field examples

- `id`: Example: `"spark-runtime-4.0.0-getting-started"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `pageKind`: Example: `"docsPage"`
- `section`: Example: `"documentation"`
- `originKey`: Example: `"archive"`
- `path`: Example: `"/spark/4.0.0/docs/getting-started/"`
- `title`: Example: `"Getting Started"`
- `linkTitle`: Example: `"Start"`
- `weight`: Example: `100`
- `parentId`: Example: `"spark-runtime-4.0.0-docs-root"`
- `ancestorIds`: Example: `["spark-runtime-4.0.0-docs-root","spark-runtime-root"]`
- `versionLabel`: Example: `"4.0.0"`
- `releaseLine`: Example: `"4.0"`
- `supportStatus`: Example: `"supported"`
- `locale`: Example: `"en"`
- `translationKey`: Example: `"spark-overview"`
- `maturity`: Example: `"stable"`
- `candidateSequence`: Example: `1`
- `voteStatus`: Example: `"passed"`

<a id="latestcandidatesummary"></a>
### LatestCandidateSummary

Compact latest-candidate summary embedded in artifact aggregates.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="latestcandidatesummary-version"></a>`version` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Candidate version string when the provider exposes one. |
| <a id="latestcandidatesummary-displayversion"></a>`displayVersion` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable candidate label when it should differ from the raw version string. |
| <a id="latestcandidatesummary-candidatesequence"></a>`candidateSequence` | int | no | Numeric ordering hint for the candidate, usually the `rc` sequence number. |
| <a id="latestcandidatesummary-votestatus"></a>`voteStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Vote-status label for the latest candidate when it is known. |

#### Selected field examples

- `version`: Example: `"4.1.0-rc1"`
- `candidateSequence`: Example: `1`
- `voteStatus`: Example: `"passed"`

<a id="latestreleasesummary"></a>
### LatestReleaseSummary

Compact latest-release summary embedded in artifact aggregates.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="latestreleasesummary-version"></a>`version` | [VersionString](../pipeline-shared-types-reference/#versionstring) | yes | Exact version string of the latest known release. |
| <a id="latestreleasesummary-displayversion"></a>`displayVersion` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable label for the latest release when it should differ from the raw version string. |
| <a id="latestreleasesummary-tag"></a>`tag` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Tag associated with the latest release, if known. |
| <a id="latestreleasesummary-publicationstate"></a>`publicationState` | [PublicationState](../pipeline-shared-types-reference/#publicationstate) | no | Publication-state label for the latest release, such as published or withdrawn. |
| <a id="latestreleasesummary-publishedat"></a>`publishedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp when the latest release became publicly available. |

#### Selected field examples

- `version`: Example: `"4.0.1"`
- `tag`: Example: `"v4.0.1"`

<a id="mountaggregateentry"></a>
### MountAggregateEntry

Entry in `data/mounts.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountaggregateentry-mountid"></a>`mountId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Stable aggregate identifier for the mount entry. |
| <a id="mountaggregateentry-ownerid"></a>`ownerId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Aggregate identifier for the component or artifact that owns the mount. |
| <a id="mountaggregateentry-kind"></a>`kind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Short mount kind label that tells consumers what sort of subtree this is. |
| <a id="mountaggregateentry-trustclass"></a>`trustClass` | [TrustClass](../pipeline-shared-types-reference/#trustclass) | yes | Trust level assigned to the mounted content. |
| <a id="mountaggregateentry-publicpath"></a>`publicPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public path where the mounted subtree is published. |
| <a id="mountaggregateentry-sourceref"></a>`sourceRef` | [MountSourceRef](../pipeline-shared-types-reference/#mountsourceref) | yes | Typed source reference for the generated or imported subtree being mounted. |
| <a id="mountaggregateentry-versioncontext"></a>`versionContext` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional version-context label that scopes the mount to one publication context. |
| <a id="mountaggregateentry-indexbehavior"></a>`indexBehavior` | [IndexBehavior](../pipeline-shared-types-reference/#indexbehavior) | no | How the mounted subtree should participate in generated indexes or listings. |
| <a id="mountaggregateentry-metadata"></a>`metadata` | [ExtensionsObject](../pipeline-shared-types-reference/#extensionsobject) | no | Small JSON-like extension object for extra mount metadata consumed by downstream tooling. |

#### Selected field examples

- `mountId`: Example: `"spark-runtime-generated-api"`
- `ownerId`: Example: `"artifact:spark/runtime"`
- `kind`: Example: `"generatedApi"`
- `publicPath`: Example: `"/spark/api/"`
- `sourceRef`: Example: `"generated/api"`
- `versionContext`: Example: `"release"`

<a id="providersdataentry"></a>
### ProvidersDataEntry

Entry in `data/providers.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providersdataentry-key"></a>`key` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | yes | Stable provider identifier used by aggregate entries that originate from this provider. |
| <a id="providersdataentry-type"></a>`type` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Provider implementation type, such as `github` or another fetcher backend label. |
| <a id="providersdataentry-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable provider label shown in generated metadata or diagnostics. |
| <a id="providersdataentry-baseurl"></a>`baseUrl` | [ProviderBaseUrl](../pipeline-shared-types-reference/#providerbaseurl) | no | Base URL of the provider service when records can link back to a human-browsable upstream origin. |
| <a id="providersdataentry-fetchedat"></a>`fetchedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | yes | Timestamp when this provider descriptor was fetched or refreshed. |

#### Selected field examples

- `key`: Example: `"github-releases"`
- `type`: Example: `"github"`
- `displayName`: Example: `"GitHub Releases"`

<a id="redirectaggregateentry"></a>
### RedirectAggregateEntry

Entry in `data/redirects.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="redirectaggregateentry-fromurl"></a>`fromUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute source URL that should redirect. |
| <a id="redirectaggregateentry-tourl"></a>`toUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute destination URL that the redirect should send readers to. |
| <a id="redirectaggregateentry-status"></a>`status` | int | yes | HTTP redirect status code emitted for this redirect. |
| <a id="redirectaggregateentry-reason"></a>`reason` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short explanation of why the redirect exists. |
| <a id="redirectaggregateentry-sourcekind"></a>`sourceKind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short label describing where the redirect originated, such as an alias or withdrawn release rule. |

#### Selected field examples

- `status`: Example: `308`
- `sourceKind`: Example: `"withdrawnRelease"`

<a id="refaggregateentry"></a>
### RefAggregateEntry

Entry in `data/refs.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="refaggregateentry-provider"></a>`provider` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | no | Provider key for the upstream system that supplied this ref record. |
| <a id="refaggregateentry-externalid"></a>`externalId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Provider-specific stable identifier for the upstream ref record. |
| <a id="refaggregateentry-externalurl"></a>`externalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Human-browsable upstream URL for the ref record. |
| <a id="refaggregateentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the ref context. |
| <a id="refaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Owning artifact key for the ref context. |
| <a id="refaggregateentry-kind"></a>`kind` | [RecordKind](../pipeline-shared-types-reference/#recordkind) | yes | Ref context kind, limited to development, named-ref, and line-head entries. |
| <a id="refaggregateentry-namedrefkey"></a>`namedRefKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Catalog-authored named-ref key when this entry represents a named ref. |
| <a id="refaggregateentry-ref"></a>`ref` | [RefString](../pipeline-shared-types-reference/#refstring) | yes | Exact source-control ref for the published ref context. |
| <a id="refaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable label for the ref context. |
| <a id="refaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key when the ref context represents a line head. |
| <a id="refaggregateentry-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Maturity label associated with the ref context. |

#### Selected field examples

- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `namedRefKey`: Example: `"preview"`
- `ref`: Example: `"refs/heads/main"`
- `displayVersion`: Example: `"main"`
- `releaseLine`: Example: `"4.0"`
- `maturity`: Example: `"preview"`

<a id="releaseaggregateentry"></a>
### ReleaseAggregateEntry

Entry in `data/releases.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaseaggregateentry-provider"></a>`provider` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | no | Provider key for the upstream system that supplied this release record. |
| <a id="releaseaggregateentry-externalid"></a>`externalId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Provider-specific stable identifier for the upstream release record. |
| <a id="releaseaggregateentry-externalurl"></a>`externalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Human-browsable upstream URL for the release record. |
| <a id="releaseaggregateentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the release. |
| <a id="releaseaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Owning artifact key for the release. |
| <a id="releaseaggregateentry-version"></a>`version` | [VersionString](../pipeline-shared-types-reference/#versionstring) | yes | Exact released version represented by this aggregate entry. |
| <a id="releaseaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable version label when it should differ from the raw version string. |
| <a id="releaseaggregateentry-tag"></a>`tag` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Exact tag associated with the release, if known. |
| <a id="releaseaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key that groups this release with related versions. |
| <a id="releaseaggregateentry-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Ancestor release-line keys ordered from nearest to farthest. |
| <a id="releaseaggregateentry-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label associated with the release. |
| <a id="releaseaggregateentry-supportwindow"></a>`supportWindow` | [SupportWindow](../pipeline-authored-input-reference/#supportwindow) | no | Lifecycle dates and support notes associated with the release. |
| <a id="releaseaggregateentry-publicationstate"></a>`publicationState` | [PublicationState](../pipeline-shared-types-reference/#publicationstate) | no | Publication-state label for the release, such as published, withdrawn, or tombstoned. |
| <a id="releaseaggregateentry-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](../pipeline-shared-types-reference/#withdrawalbehavior) | no | Behavior that readers should experience when the release has been withdrawn. |
| <a id="releaseaggregateentry-redirecttarget"></a>`redirectTarget` | [ReferenceString](../pipeline-shared-types-reference/#referencestring) \| [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Replacement route or external URL used when a withdrawn release redirects readers elsewhere. |
| <a id="releaseaggregateentry-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Maturity label such as stable, preview, or beta. |
| <a id="releaseaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Timestamp when the release became publicly available. |
| <a id="releaseaggregateentry-assets"></a>`assets` | list[[ProviderAsset](../pipeline-provider-input-reference/#providerasset)] | no | Downloadable assets attached to the release. |
| <a id="releaseaggregateentry-urls"></a>`urls` | dict[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring), [UrlString](../pipeline-shared-types-reference/#urlstring)] | no | Additional named URLs related to the release, such as notes, downloads, or verification material. |

#### Selected field examples

- `provider`: Example: `"github-releases"`
- `externalId`: Example: `"github:release:runtime-4.0.0"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `version`: Example: `"4.0.0"`
- `tag`: Example: `"v4.0.0"`
- `releaseLine`: Example: `"4.0"`
- `releaseLineAncestors`: Example: `["4.x","stable"]`
- `supportStatus`: Example: `"supported"`
- `redirectTarget`: Example: `"route:/spark/releases/4.0.1/"`
- `maturity`: Example: `"stable"`

<a id="routeaggregateentry"></a>
### RouteAggregateEntry

Entry in `data/routes.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="routeaggregateentry-originkey"></a>`originKey` | [OriginKey](../pipeline-shared-types-reference/#originkey) | yes | Origin key that this public route belongs to. |
| <a id="routeaggregateentry-baseurl"></a>`baseUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Base URL for the route's origin. |
| <a id="routeaggregateentry-path"></a>`path` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public path for the route. |
| <a id="routeaggregateentry-url"></a>`url` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the route after joining `baseUrl` and `path`. |
| <a id="routeaggregateentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the route. |
| <a id="routeaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | no | Owning artifact key when the route belongs to a specific artifact. |
| <a id="routeaggregateentry-section"></a>`section` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Higher-level section label for the route, if present. |
| <a id="routeaggregateentry-canonical"></a>`canonical` | bool | no | Whether this route should be treated as the canonical route among equivalent alternatives. |
| <a id="routeaggregateentry-routekind"></a>`routeKind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short route-kind label such as component root, docs root, alias, or release page. |
| <a id="routeaggregateentry-targetid"></a>`targetId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Stable target identifier used to correlate equivalent routes or aliases. |
| <a id="routeaggregateentry-label"></a>`label` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable label for the route, if present. |
| <a id="routeaggregateentry-locale"></a>`locale` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Locale key when the route belongs to a localized page family. |

#### Selected field examples

- `originKey`: Example: `"archive"`
- `path`: Example: `"/spark/4.0.0/docs/"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `section`: Example: `"documentation"`
- `routeKind`: Example: `"docsRoot"`
- `targetId`: Example: `"spark-runtime-4.0.0-docs"`
- `label`: Example: `"4.0 docs"`
- `locale`: Example: `"en"`

<a id="translationsetaggregateentry"></a>
### TranslationSetAggregateEntry

Entry in `data/translations.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="translationsetaggregateentry-translationkey"></a>`translationKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Shared key that ties all translated sibling pages in this set together. |
| <a id="translationsetaggregateentry-componentslug"></a>`componentSlug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Owning component slug for the translation set. |
| <a id="translationsetaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | no | Owning artifact key when the translation set belongs to a specific artifact. |
| <a id="translationsetaggregateentry-entries"></a>`entries` | list[[TranslationLinkSummary](../pipeline-staged-front-matter-reference/#translationlinksummary)] | yes | Translated sibling pages that belong to the same translation set. |

#### Selected field examples

- `translationKey`: Example: `"spark-overview"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`

