---
weight: 30
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

# Pipeline model schema reference

This reference is generated from the Site Pipeline Pydantic models and checked-in reference metadata. Do not edit it by hand; regenerate it with `make schemas`.

This reference describes the current public contracts exposed by the Site Pipeline model layer.
It covers authored inputs, provider inputs, pipeline-emitted outputs, shared scalars, enums, and the detailed field rules for each typed contract.
Use the contract-file tables to find the governing file or schema root, then use the linked type sections below for the exact field-level contract.

## How to read this reference

- contract-file tables identify the stable on-disk file for each root contract, if applicable
- field names are shown in their wire-format aliases
- type, enum, and scalar names link to their definitions below
- schema files are listed by checked-in filename for the matching root contract

## File contract index

### Authored input contracts

Consumer-owned and component-owned source-tree contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/component.yaml` | [ComponentMetadataDocumentV1](#componentmetadatadocumentv1) | `site-pipeline-component-v1.schema.json` | Stable component identity, repository content roots, and shared lifecycle hints. |
| `site/catalog.yaml` | [SiteCatalogDocumentV1](#sitecatalogdocumentv1) | `site-pipeline-catalog-v1.schema.json` | Catalog of components, defaults, sources, origins, and publication rules for one site. |

### Provider input contracts

Provider-derived snapshot contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/provider-snapshot.json` | [ProviderSnapshotDocumentV1](#providersnapshotdocumentv1) | `site-pipeline-provider-snapshot-v1.schema.json` | Normalized provider inventory of releases, candidates, refs, and downloadable assets. |

### Pipeline-emitted file contracts

Stable files that the pipeline writes into staged or published output trees.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `data/_pipeline/aggregate-dependencies.json` | [AggregateDependencyMapV1](#aggregatedependencymapv1) | `site-pipeline-aggregate-dependencies-v1.schema.json` | Coordinator aggregate files and the units that can invalidate them. |
| `data/_pipeline/output-ownership.json` | [OutputOwnershipMapV1](#outputownershipmapv1) | `site-pipeline-output-ownership-v1.schema.json` | Ownership map for staged files and directories retained across rebuilds. |
| `data/_pipeline/unit-contributions.json` | [PersistedUnitContributionsV1](#persistedunitcontributionsv1) | `site-pipeline-unit-contributions-v1.schema.json` | Per-unit page contribution manifests retained in the visible stage. |
| `data/artifacts.json` | [ArtifactsDataEntry](#artifactsdataentry) | `site-pipeline-artifacts-data-v1.schema.json` | Published artifact inventory with version discovery rules, lifecycle hints, and latest-version summaries. |
| `data/candidates.json` | [CandidateAggregateEntry](#candidateaggregateentry) | `site-pipeline-candidates-data-v1.schema.json` | Published release-candidate inventory with vote status and downloadable assets. |
| `data/compatibility.json` | [CompatibilityAggregateEntry](#compatibilityaggregateentry) | `site-pipeline-compatibility-data-v1.schema.json` | Declared compatibility relationships between published identities. |
| `data/components.json` | [ComponentsDataEntry](#componentsdataentry) | `site-pipeline-components-data-v1.schema.json` | Published component inventory with resolved routes, origins, and artifact summaries. |
| `data/content-index.json` | [ContentIndexEntry](#contentindexentry) | `site-pipeline-content-index-data-v1.schema.json` | Search and navigation index for staged pages with titles, ancestry, and version metadata. |
| `data/diagnostics.json` | [PipelineDiagnosticEntry](#pipelinediagnosticentry) | `site-pipeline-diagnostics-data-v1.schema.json` | Structured diagnostics emitted during planning, checking, or staging. |
| `data/mounts.json` | [MountAggregateEntry](#mountaggregateentry) | `site-pipeline-mounts-data-v1.schema.json` | Mounted content and asset subtrees published under resolved public paths. |
| `data/providers.json` | [ProvidersDataEntry](#providersdataentry) | `site-pipeline-providers-data-v1.schema.json` | Loaded provider inventory with display names, base URLs, and fetch timestamps. |
| `data/redirects.json` | [RedirectAggregateEntry](#redirectaggregateentry) | `site-pipeline-redirects-data-v1.schema.json` | Flat inventory of published redirects and their resolved destination URLs. |
| `data/refs.json` | [RefAggregateEntry](#refaggregateentry) | `site-pipeline-refs-data-v1.schema.json` | Published development, line-head, and named-ref inventory for version navigation. |
| `data/releases.json` | [ReleaseAggregateEntry](#releaseaggregateentry) | `site-pipeline-releases-data-v1.schema.json` | Published released-version inventory with lifecycle, support, and asset metadata. |
| `data/routes.json` | [RouteAggregateEntry](#routeaggregateentry) | `site-pipeline-routes-data-v1.schema.json` | Flat inventory of published routes with resolved URLs, labels, and ownership metadata. |
| `data/translations.json` | [TranslationSetAggregateEntry](#translationsetaggregateentry) | `site-pipeline-translations-data-v1.schema.json` | Translation sibling groups keyed by one shared translation identifier. |
| `manifest.json` | [StageManifestV1](#stagemanifestv1) | `site-pipeline-stage-manifest-v1.schema.json` | Entry point for a stage tree, including roots, formats, and aggregate file locations. |

### Pipeline-emitted non-file root contracts

Schema-root report and namespace types that do not correspond to one stable checked-in file path.

| Root type(s) | Schema file | Summary |
| --- | --- | --- |
| [CheckReportV1](#checkreportv1) | `site-pipeline-check-report-v1.schema.json` | Validation result for one `site-pipeline check` invocation. |
| [PipelineFrontMatterNamespace](#pipelinefrontmatternamespace) | `site-pipeline-front-matter-namespace-v1.schema.json` | Reserved front matter namespace containing pipeline-derived component and page metadata. |
| [ResolvedMaterializationReportV1](#resolvedmaterializationreportv1) | `site-pipeline-materialization-report-v1.schema.json` | Planning inventory of required local inputs and their current materialization status. |
| [StageRunReportV1](#stagerunreportv1) | `site-pipeline-stage-run-report-v1.schema.json` | Execution result for one `build` run or completed watch cycle. |

## Scalar aliases

| Type | Base type | Description |
| --- | --- | --- |
| <a id="nonemptystring"></a>`NonEmptyString` | `String` | Non-empty free-form string. |
| <a id="nonnegativeinteger"></a>`NonNegativeInteger` | `Integer` | Integer value greater than or equal to zero. |
| <a id="positiveinteger"></a>`PositiveInteger` | `Integer` | Integer value greater than zero. |
| <a id="identifier"></a>`Identifier` | `String` | Non-empty symbolic key. |
| <a id="slug"></a>`Slug` | `String` | Stable component identifier. |
| <a id="artifactkey"></a>`ArtifactKey` | `String` | Stable artifact identifier unique within a component. |
| <a id="originkey"></a>`OriginKey` | `Identifier` | Key for a publication origin. |
| <a id="sourcekey"></a>`SourceKey` | `String` | Key for a source or repository entry. |
| <a id="providerkey"></a>`ProviderKey` | `String` | Key for a provider descriptor. |
| <a id="versionstring"></a>`VersionString` | `String` | Exact version string such as `4.0.0`. |
| <a id="refstring"></a>`RefString` | `String` | Moving ref name such as `main` or `releases/4.x`. |
| <a id="referencestring"></a>`ReferenceString` | `String` | Typed internal reference string such as `route:/docs/latest/` or `artifact:spark/runtime`. |
| <a id="regexstring"></a>`RegexString` | `String` | Regex pattern stored as text. |
| <a id="schemaversion"></a>`SchemaVersion` | `Integer` | Positive schema version integer. |
| <a id="timestampstring"></a>`TimestampString` | `Datetime` | RFC 3339 / ISO 8601 timestamp value. |
| <a id="localpathstring"></a>`LocalPathString` | `String` | Consumer-local filesystem path that follows host operating-system path rules. |
| <a id="reporelativepath"></a>`RepoRelativePath` | `String` | Repository-relative normalized POSIX path that must use forward slashes. |
| <a id="stagerelativepath"></a>`StageRelativePath` | `String` | Stage-root-relative normalized POSIX path that must use forward slashes. |
| <a id="mountsourceref"></a>`MountSourceRef` | `String` | Stable mount source reference such as a path or bundle key. |
| <a id="publicpath"></a>`PublicPath` | `String` | Resolved normalized POSIX public path such as `/docs/latest/`. |
| <a id="hostnamestring"></a>`HostnameString` | `String` | Hostname derived from an origin URL. |
| <a id="urlstring"></a>`UrlString` | `String` | Absolute public URL. |
| <a id="providerbaseurl"></a>`ProviderBaseUrl` | `String` | Validated public provider base URL. |
| <a id="extensionsobject"></a>`ExtensionsObject` | `Object` | Opaque structured metadata allowed only in explicitly documented extension slots. |


## Shared enums

| Type | Values | Description |
| --- | --- | --- |
| <a id="candidateselectionmode"></a>`CandidateSelectionMode` | `none`, `latest`, `explicit` | Strategy used to select a candidate version. |
| <a id="checkfailurethreshold"></a>`CheckFailureThreshold` | `error`, `warning` | Lowest severity that causes ``check`` to fail. |
| <a id="diagnosticseverity"></a>`DiagnosticSeverity` | `info`, `warning`, `error` | Severity level for pipeline diagnostics. |
| <a id="indexbehavior"></a>`IndexBehavior` | `full`, `metadataOnly`, `none` | Renderer hint for version/ref index visibility. |
| <a id="lineheadselectionmode"></a>`LineHeadSelectionMode` | `none`, `allAuthored`, `explicit` | Strategy used to derive a release-line head record. |
| <a id="materializationinputkind"></a>`MaterializationInputKind` | `sitePages`, `siteAssets`, `vendorAssets`, `development`, `namedRef`, `lineHead`, `candidate`, `released` | Planning/build/watch local-input category. |
| <a id="materializationstatus"></a>`MaterializationStatus` | `present`, `missing`, `stale`, `unresolved` | Readiness state of a required local input. |
| <a id="planningtarget"></a>`PlanningTarget` | `build`, `watch` | Planning intent for later staging behavior. |
| <a id="publicationstate"></a>`PublicationState` | `published`, `hidden`, `withdrawn`, `tombstoned` | Observed provider-side publication state. |
| <a id="recordkind"></a>`RecordKind` | `development`, `released`, `candidate`, `namedRef`, `lineHead` | Normalized provider record lifecycle kind. |
| <a id="releaseselectionmode"></a>`ReleaseSelectionMode` | `latestPerLine`, `latestN`, `allKnown`, `explicit` | Strategy used to select a released version. |
| <a id="routemode"></a>`RouteMode` | `none`, `prefixAll` | Locale routing strategy for a published route set. |
| <a id="runstatus"></a>`RunStatus` | `clean`, `warnings`, `errors` | Overall diagnostic class for a run or cycle. |
| <a id="stagecommand"></a>`StageCommand` | `build`, `watch` | Stable stage-producing command modes. |
| <a id="trustclass"></a>`TrustClass` | `passive`, `active` | Trust posture of a mounted content subtree. |
| <a id="withdrawalbehavior"></a>`WithdrawalBehavior` | `notice`, `redirect`, `omit` | Author-directed behavior for a withdrawn release. |


## Type index

### Authored input types

Consumer-owned and component-owned authored contract models.

- [ArtifactConfig](#artifactconfig) — One independently versioned release unit inside a component.
- [ArtifactLifecycleConfig](#artifactlifecycleconfig) — Lifecycle metadata for an artifact's stable versions, release lines, and support policy.
- [ArtifactVersioningConfig](#artifactversioningconfig) — How the pipeline discovers development, maintenance, tag, and named-ref versions.
- [CandidateSelectionPolicy](#candidateselectionpolicy) — Rule for which release candidates should become published contexts.
- [CatalogDefaults](#catalogdefaults) — Shared defaults applied before per-component overrides.
- [CompatibilityAssertionConfig](#compatibilityassertionconfig) — Compatibility statement between two published identities, such as an artifact and a supported platform.
- [ComponentCatalogEntry](#componentcatalogentry) — Component entry in the consumer catalog.
- [ComponentContentSelection](#componentcontentselection) — Source selection for a component's shared pages, docs, and assets.
- [ComponentIdentity](#componentidentity) — Stable identity for a component repository.
- [ComponentLifecycleHints](#componentlifecyclehints) — Optional lifecycle defaults shared across all artifacts in a component repository.
- [ComponentMetadataDocumentV1](#componentmetadatadocumentv1) — Canonical component metadata that defines stable identity, repository content roots, and optional lifecycle defaults shared across a component repository.
- [ContentRoots](#contentroots) — Repository-relative locations of authored component content.
- [ExactReleaseConfig](#exactreleaseconfig) — Per-version lifecycle metadata and publication overrides for one exact release.
- [GroupConfig](#groupconfig) — Reusable defaults and grouping hints shared by several components.
- [LineHeadSelectionPolicy](#lineheadselectionpolicy) — Rule for which release-line head refs should appear as publishable contexts.
- [LocalizationConfig](#localizationconfig) — Locale and translation defaults.
- [MountConfig](#mountconfig) — Mounted subtree, such as generated API docs or imported assets, published below one public path.
- [NamedRefConfig](#namedrefconfig) — Named source-control ref intentionally exposed as a stable version context.
- [OriginConfig](#originconfig) — Named public base URL that published routes can resolve against.
- [PublicationConfig](#publicationconfig) — Resolved-or-authored route layout choices for a component or artifact.
- [PublicationSelectionPolicy](#publicationselectionpolicy) — Planning-time rule set for which version contexts are staged and linked.
- [RedirectRuleConfig](#redirectruleconfig) — Redirect rule that sends one published path to another internal or external target.
- [ReleaseLineConfig](#releaselineconfig) — One logical release line, such as `4.0`, together with its lifecycle metadata.
- [ReleaseSelectionPolicy](#releaseselectionpolicy) — Rule for which exact released versions should become published contexts.
- [RouteAliasConfig](#routealiasconfig) — Additional public route that resolves to the same published destination.
- [SiteCatalogDocumentV1](#sitecatalogdocumentv1) — Canonical site catalog that lists participating components, shared defaults, source bindings, publication origins, and publication policy for one site.
- [SiteContentConfig](#sitecontentconfig) — Top-level pages and asset trees that belong to the site as a whole.
- [SourceConfig](#sourceconfig) — Named repository or checkout binding reused by components and artifacts.
- [SupportStatusDefinition](#supportstatusdefinition) — One reusable support-status label, description, and default lifecycle behavior.
- [SupportWindow](#supportwindow) — Lifecycle dates and support notes for one release line or exact release.

### Provider input types

Normalized provider snapshot contracts consumed by the pipeline.

- [ProviderAsset](#providerasset) — Downloadable asset attached to one provider release or candidate record.
- [ProviderDescriptor](#providerdescriptor) — Metadata about one provider that contributed records to the snapshot.
- [ProviderRecord](#providerrecord) — Normalized provider fact about one release, candidate, or ref context.
- [ProviderSnapshotDocumentV1](#providersnapshotdocumentv1) — Provider-derived normalized snapshot from ``site/provider-snapshot.json``.

### Planning and stage-contract types

Pipeline-emitted planning, diagnostics, and stage-manifest contracts.

- [CheckReportV1](#checkreportv1) — Machine-readable result of ``site-pipeline check``.
- [CheckSummary](#checksummary) — Outcome counts and pass/fail decision for one `check` run.
- [PipelineDiagnosticEntry](#pipelinediagnosticentry) — Structured diagnostic emitted during planning, checking, or staging.
- [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) — Compact placeholder used when full diagnostic details were too large to keep.
- [ResolvedMaterializationEntry](#resolvedmaterializationentry) — One local checkout or fetched input that the planner expects to exist.
- [ResolvedMaterializationReportV1](#resolvedmaterializationreportv1) — Machine-readable planning report for required local inputs.
- [StageDataFiles](#stagedatafiles) — Stage-relative paths of aggregate metadata files currently present in one stage tree.
- [StageManifestV1](#stagemanifestv1) — Authoritative entry-point document for a staged output tree.
- [StageRoots](#stageroots) — Named top-level directories inside a stage tree.
- [StageRunReportV1](#stagerunreportv1) — Machine-readable result of ``build`` or one completed watch cycle.
- [StageRunSummary](#stagerunsummary) — Outcome counts and usability flags for one stage-producing run or watch cycle.

### Staged front matter types

Front matter and page-level metadata emitted into staged content.

- [ArtifactFrontMatterSummary](#artifactfrontmattersummary) — Small artifact summary embedded in component front matter.
- [PipelineComponentFrontMatter](#pipelinecomponentfrontmatter) — Component-level pipeline metadata injected into staged page front matter.
- [PipelineFrontMatterNamespace](#pipelinefrontmatternamespace) — Reserved top-level front matter namespace that the pipeline injects into staged pages.
- [PipelinePageFrontMatter](#pipelinepagefrontmatter) — Page-local pipeline metadata injected into staged page front matter.
- [ProviderProvenance](#providerprovenance) — Small pointer back to the provider record that informed this page's version.
- [ReleaseLineContext](#releaselinecontext) — Release-line context attached to one staged page's current version.
- [ReleaseLineSummary](#releaselinesummary) — Small release-line summary embedded into page or component front matter.
- [ResolvedOrigin](#resolvedorigin) — Resolved origin details for the current publication target.
- [ResolvedPathSet](#resolvedpathset) — Resolved public path roots for a component.
- [ResolvedPublication](#resolvedpublication) — Resolved origin, path roots, and absolute URLs for a component.
- [ResolvedUrlSet](#resolvedurlset) — Resolved absolute URLs for a component.
- [TranslationLinkSummary](#translationlinksummary) — Compact link to one translated sibling page.
- [VersionContext](#versioncontext) — Version, release-candidate, or ref context attached to one staged page.

### Staged aggregate metadata types

Public aggregate JSON contracts emitted under `data/`.

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

### Incremental bookkeeping types

Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`.

- [AggregateDependencyEntryV1](#aggregatedependencyentryv1) — One coordinator-owned aggregate and the units that may change its payload.
- [AggregateDependencyMapV1](#aggregatedependencymapv1) — Shared-output dependency map for the current first-wave coordinator outputs.
- [OutputOwnershipClaimV1](#outputownershipclaimv1) — One exact published file or directory root together with its logical owner.
- [OutputOwnershipMapV1](#outputownershipmapv1) — Published ownership inventory used to prune retained stages safely.
- [PersistedUnitContributionsV1](#persistedunitcontributionsv1) — Stable per-unit page contribution manifests retained in the visible stage.
- [StagedPageContributionWire](#stagedpagecontributionwire) — Metadata emitted by one page-staging worker for later aggregation.
- [UnitContributionManifestWire](#unitcontributionmanifestwire) — Worker-emitted contribution fragment consumed by the coordinator.

## Authored input types

Consumer-owned and component-owned authored contract models.

<a id="artifactconfig"></a>
### ArtifactConfig

One independently versioned release unit inside a component.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactconfig-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | Stable artifact identifier used in typed references, staged metadata, and provider records. |
| <a id="artifactconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable artifact label shown to readers when the raw key is not ideal UI text. |
| <a id="artifactconfig-source"></a>`source` | [SourceKey](#sourcekey) | yes | Named source entry that owns the versioned docs and assets for this artifact. |
| <a id="artifactconfig-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) | no | Artifact-specific docs root that overrides any inherited docs location when versioned docs live in a custom subdirectory. |
| <a id="artifactconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) | no | Artifact-specific asset root that overrides inherited component asset locations for this artifact's versioned output. |
| <a id="artifactconfig-versioning"></a>`versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | yes | Rules for discovering development refs, maintenance refs, tags, and named refs for this artifact. |
| <a id="artifactconfig-publicationselection"></a>`publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) | no | Artifact-specific override for which version contexts should be staged and published. |
| <a id="artifactconfig-lifecycle"></a>`lifecycle` | [ArtifactLifecycleConfig](#artifactlifecycleconfig) | no | Lifecycle metadata for stable versions, release lines, and support policy for this artifact. |
| <a id="artifactconfig-compatibility"></a>`compatibility` | list[[CompatibilityAssertionConfig](#compatibilityassertionconfig)] | no | Compatibility statements that should be emitted for this artifact in staged metadata. |
| <a id="artifactconfig-mounts"></a>`mounts` | list[[MountConfig](#mountconfig)] | no | Mounted generated or imported subtrees that belong to this artifact's published surface. |

#### Selected field examples

- `key`: Example: `"runtime"`
- `displayName`: Example: `"Runtime"`
- `source`: Example: `"apache-spark"`
- `docsRoot`: Example: `"docs/runtime"`
- `assetsRoot`: Example: `"docs/runtime/assets"`

<a id="artifactlifecycleconfig"></a>
### ArtifactLifecycleConfig

Lifecycle metadata for an artifact's stable versions, release lines, and support policy.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactlifecycleconfig-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | Most recent stable version that readers should treat as the default recommendation for this artifact. |
| <a id="artifactlifecycleconfig-releaselines"></a>`releaseLines` | list[[ReleaseLineConfig](#releaselineconfig)] | no | Release-line definitions for this artifact, including latest versions and optional support metadata. |
| <a id="artifactlifecycleconfig-releases"></a>`releases` | list[[ExactReleaseConfig](#exactreleaseconfig)] | no | Per-version lifecycle metadata and publication overrides for exact released versions. |
| <a id="artifactlifecycleconfig-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](#identifier), [SupportStatusDefinition](#supportstatusdefinition)] | no | Reusable support-status definitions that release lines and exact releases can refer to by key. |
| <a id="artifactlifecycleconfig-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) | no | Canonical URL for the support policy document that readers should consult for this artifact. |
| <a id="artifactlifecycleconfig-defaultsupportwindow"></a>`defaultSupportWindow` | [SupportWindow](#supportwindow) | no | Fallback lifecycle window applied when a line or exact release does not provide a more specific support window. |

#### Selected field examples

- `latestStable`: Example: `"4.0.1"`

<a id="artifactversioningconfig"></a>
### ArtifactVersioningConfig

How the pipeline discovers development, maintenance, tag, and named-ref versions.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactversioningconfig-developmentref"></a>`developmentRef` | [RefString](#refstring) | yes | Source-control ref that represents the moving development docs for this artifact. |
| <a id="artifactversioningconfig-maintenancerefpattern"></a>`maintenanceRefPattern` | [NonEmptyString](#nonemptystring) | no | Pattern used to derive maintenance branch refs from a release-line key, usually with `{line}` as the substitution placeholder. |
| <a id="artifactversioningconfig-tagpattern"></a>`tagPattern` | [RegexString](#regexstring) | yes | Regular expression used to recognize provider tags that belong to this artifact's version stream. |
| <a id="artifactversioningconfig-namedrefs"></a>`namedRefs` | list[[NamedRefConfig](#namedrefconfig)] | no | Additional intentionally named version contexts, such as preview or stable branches, that should be selectable by key. |

#### Selected field examples

- `developmentRef`: Example: `"main"`
- `maintenanceRefPattern`: Example: `"release/{line}"`
- `tagPattern`: Example: `"^v[0-9]+\\.[0-9]+\\.[0-9]+$"`

<a id="candidateselectionpolicy"></a>
### CandidateSelectionPolicy

Rule for which release candidates should become published contexts.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="candidateselectionpolicy-mode"></a>`mode` | [CandidateSelectionMode](#candidateselectionmode) | yes | Selection strategy for candidate releases, such as disabling them or selecting an explicit set. |
| <a id="candidateselectionpolicy-versions"></a>`versions` | list[[VersionString](#versionstring)] | no | Candidate version strings to include when `mode` is `explicit` and provider versions are available. |
| <a id="candidateselectionpolicy-externalids"></a>`externalIds` | list[[NonEmptyString](#nonemptystring)] | no | Provider-specific candidate identifiers to include when version strings alone are not enough to identify the desired candidate records. |

#### Selected field examples

- `versions`: Example: `["4.1.0-rc1"]`
- `externalIds`: Example: `["github:runtime-4.1.0-rc1"]`

<a id="catalogdefaults"></a>
### CatalogDefaults

Shared defaults applied before per-component overrides.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="catalogdefaults-metadatafile"></a>`metadataFile` | [RepoRelativePath](#reporelativepath) | no | Default location of `site/component.yaml` within each source tree. |
| <a id="catalogdefaults-pagesroot"></a>`pagesRoot` | [RepoRelativePath](#reporelativepath) | no | Default repository-relative root for non-versioned component pages. |
| <a id="catalogdefaults-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) | no | Default repository-relative root for component docs content. |
| <a id="catalogdefaults-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) | no | Default repository-relative root for component static assets. |
| <a id="catalogdefaults-publication"></a>`publication` | PublicationDefaults | no | Shared publication defaults inherited by components unless they override them. |
| <a id="catalogdefaults-localization"></a>`localization` | [LocalizationConfig](#localizationconfig) | no | Shared localization defaults inherited by components unless they override them. |

<a id="compatibilityassertionconfig"></a>
### CompatibilityAssertionConfig

Compatibility statement between two published identities, such as an artifact and a supported platform.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="compatibilityassertionconfig-subjectref"></a>`subjectRef` | [ReferenceString](#referencestring) | yes | Typed internal reference string for the thing whose compatibility is being described. |
| <a id="compatibilityassertionconfig-targetref"></a>`targetRef` | [ReferenceString](#referencestring) | yes | Typed internal reference string for the thing that the subject is compatible with or constrained by. |
| <a id="compatibilityassertionconfig-relation"></a>`relation` | [NonEmptyString](#nonemptystring) | yes | Relationship label that names the compatibility statement, such as `testedWith`, `requires`, or `incompatibleWith`. |
| <a id="compatibilityassertionconfig-scope"></a>`scope` | [NonEmptyString](#nonemptystring) | no | Optional scope label that narrows the compatibility statement to one subsystem, API surface, or deployment mode. |
| <a id="compatibilityassertionconfig-confidence"></a>`confidence` | [NonEmptyString](#nonemptystring) | no | Optional confidence label that tells readers how strong or direct the supporting evidence is. |
| <a id="compatibilityassertionconfig-notes"></a>`notes` | [NonEmptyString](#nonemptystring) | no | Additional human-readable explanation, caveats, or migration advice for the compatibility statement. |

#### Selected field examples

- `subjectRef`: Example: `"artifact:spark/runtime"`
- `targetRef`: Example: `"artifact:spark/operator"`
- `relation`: Example: `"testedWith"`
- `scope`: Example: `"kubernetes"`
- `confidence`: Example: `"verified"`

<a id="componentcatalogentry"></a>
### ComponentCatalogEntry

Component entry in the consumer catalog.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentcatalogentry-slug"></a>`slug` | [Slug](#slug) | yes | Stable component identifier. |
| <a id="componentcatalogentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable component name override or convenience value. |
| <a id="componentcatalogentry-localdir"></a>`localDir` | [RepoRelativePath](#reporelativepath) | no | Simple shorthand for binding the component to one workspace-local checkout directory. |
| <a id="componentcatalogentry-weight"></a>`weight` | int | no | Optional ordering hint for component listings, menus, and other consumer-rendered component collections. |
| <a id="componentcatalogentry-group"></a>`group` | [Identifier](#identifier) | no | Optional group key for inherited defaults and renderer grouping. |
| <a id="componentcatalogentry-content"></a>`content` | [ComponentContentSelection](#componentcontentselection) | no | Shared content-source selection for component pages, docs, and assets. |
| <a id="componentcatalogentry-publication"></a>`publication` | [PublicationConfig](#publicationconfig) | no | Explicit publication configuration for this component. |
| <a id="componentcatalogentry-publicationselection"></a>`publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) | no | Default version-context selection policy inherited by contained artifacts unless they override it. |
| <a id="componentcatalogentry-localization"></a>`localization` | [LocalizationConfig](#localizationconfig) | no | Component-specific localization overrides. |
| <a id="componentcatalogentry-compatibility"></a>`compatibility` | list[[CompatibilityAssertionConfig](#compatibilityassertionconfig)] | no | Component-level compatibility assertions emitted into staged metadata. |
| <a id="componentcatalogentry-mounts"></a>`mounts` | list[[MountConfig](#mountconfig)] | no | Component-level generated or imported documentation mounts. |
| <a id="componentcatalogentry-artifacts"></a>`artifacts` | list[[ArtifactConfig](#artifactconfig)] | no | Independently versioned artifacts belonging to this component. |

<a id="componentcontentselection"></a>
### ComponentContentSelection

Source selection for a component's shared pages, docs, and assets.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentcontentselection-source"></a>`source` | [SourceKey](#sourcekey) | no | Named source that owns shared component pages, docs, and assets roots. |

<a id="componentidentity"></a>
### ComponentIdentity

Stable identity for a component repository.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentidentity-slug"></a>`slug` | [Slug](#slug) | yes | Stable component identifier used by consumer catalogs and staged metadata. |
| <a id="componentidentity-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable component name shown in rendered navigation and listings. |

<a id="componentlifecyclehints"></a>
### ComponentLifecycleHints

Optional lifecycle defaults shared across all artifacts in a component repository.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentlifecyclehints-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | Latest stable version for the component when one overall release line is enough. |
| <a id="componentlifecyclehints-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](#identifier), [SupportStatusDefinition](#supportstatusdefinition)] | no | Optional support-status vocabulary shared by artifacts in this repository. |

<a id="componentmetadatadocumentv1"></a>
### ComponentMetadataDocumentV1

Canonical component metadata that defines stable identity, repository content roots, and optional lifecycle defaults shared across a component repository.

- category: `authored`
- ownership: `component-owned`
- file contract: `site/component.yaml`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentmetadatadocumentv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the component metadata file. |
| <a id="componentmetadatadocumentv1-component"></a>`component` | [ComponentIdentity](#componentidentity) | yes | Stable identity for the component repository. |
| <a id="componentmetadatadocumentv1-content"></a>`content` | [ContentRoots](#contentroots) | no | Repository-relative authored content roots owned by this component. |
| <a id="componentmetadatadocumentv1-lifecycle"></a>`lifecycle` | [ComponentLifecycleHints](#componentlifecyclehints) | no | Optional high-level lifecycle hints shared across the component repository. |

#### Content roots

Use `pagesRoot` for unversioned component pages and `docsRoot` for versioned or development docs content.

#### Example: Component metadata with identity, content roots, and lifecycle hints.

```yaml
schemaVersion: 1
component:
  slug: spark
  displayName: Apache Spark
content:
  pagesRoot: site/pages
  docsRoot: docs
lifecycle:
  latestStable: 4.0.0
  supportStatusVocabulary:
    active:
      displayName: Active
      order: 10
```

<a id="contentroots"></a>
### ContentRoots

Repository-relative locations of authored component content.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="contentroots-pagesroot"></a>`pagesRoot` | [RepoRelativePath](#reporelativepath) | no | Repository-relative root for non-versioned component-owned pages. |
| <a id="contentroots-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) | no | Repository-relative root for versioned or development docs content. |
| <a id="contentroots-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) | no | Repository-relative root for component-owned static assets. |

<a id="exactreleaseconfig"></a>
### ExactReleaseConfig

Per-version lifecycle metadata and publication overrides for one exact release.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="exactreleaseconfig-version"></a>`version` | [VersionString](#versionstring) | yes | Exact released version that this metadata entry applies to. |
| <a id="exactreleaseconfig-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key that this version belongs to when the provider data alone does not already make that relationship obvious. |
| <a id="exactreleaseconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label that should override the line-level status for this exact version. |
| <a id="exactreleaseconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes that apply only to this exact release. |
| <a id="exactreleaseconfig-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | Publication-state override for this version, such as published, withdrawn, or tombstoned. |
| <a id="exactreleaseconfig-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](#withdrawalbehavior) | no | What readers should experience when this release has been withdrawn, for example a redirect or a hard removal. |
| <a id="exactreleaseconfig-redirecttarget"></a>`redirectTarget` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | no | Replacement route or external URL to send readers to when `withdrawalBehavior` is `redirect`. |
| <a id="exactreleaseconfig-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | Human-readable explanation of the withdrawal, redirect, or support-state override for this release. |

#### Selected field examples

- `version`: Example: `"4.0.0"`
- `releaseLine`: Example: `"4.0"`
- `supportStatus`: Example: `"withdrawn"`
- `redirectTarget`: Example: `"route:/spark/releases/4.0.1/"`
- `reason`: Example: `"Superseded by 4.0.1."`

<a id="groupconfig"></a>
### GroupConfig

Reusable defaults and grouping hints shared by several components.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="groupconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable group name for renderers or generated navigation. |
| <a id="groupconfig-pathprefix"></a>`pathPrefix` | [PublicPath](#publicpath) | no | Shared public path prefix applied to grouped component publication roots. |
| <a id="groupconfig-navigationsection"></a>`navigationSection` | [NonEmptyString](#nonemptystring) | no | Optional renderer-facing grouping label for navigation or listings. |
| <a id="groupconfig-weight"></a>`weight` | int | no | Optional ordering hint shared by components in this group. |
| <a id="groupconfig-publication"></a>`publication` | [PublicationConfig](#publicationconfig) | no | Publication defaults inherited by grouped components unless they override them. |

<a id="lineheadselectionpolicy"></a>
### LineHeadSelectionPolicy

Rule for which release-line head refs should appear as publishable contexts.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="lineheadselectionpolicy-mode"></a>`mode` | [LineHeadSelectionMode](#lineheadselectionmode) | yes | Selection strategy for release-line head contexts, such as taking all lines or only an explicit subset. |
| <a id="lineheadselectionpolicy-keys"></a>`keys` | list[[NonEmptyString](#nonemptystring)] | no | Explicit release-line keys to publish when `mode` is `explicit`. |

#### Selected field examples

- `keys`: Example: `["3.5","4.0"]`

<a id="localizationconfig"></a>
### LocalizationConfig

Locale and translation defaults.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="localizationconfig-defaultlocale"></a>`defaultLocale` | [NonEmptyString](#nonemptystring) | no | Default locale used when a page does not declare a more specific locale. |
| <a id="localizationconfig-supportedlocales"></a>`supportedLocales` | list[[NonEmptyString](#nonemptystring)] | no | Supported locale keys for this site or component. |
| <a id="localizationconfig-routemode"></a>`routeMode` | [RouteMode](#routemode) | no | How localized pages should be routed within the published URL space. |
| <a id="localizationconfig-fallbacklocale"></a>`fallbackLocale` | [NonEmptyString](#nonemptystring) | no | Fallback locale used when a requested translation is unavailable. |

<a id="mountconfig"></a>
### MountConfig

Mounted subtree, such as generated API docs or imported assets, published below one public path.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountconfig-source"></a>`source` | [MountSourceRef](#mountsourceref) | yes | Typed source reference that identifies the generated or imported subtree to mount. |
| <a id="mountconfig-mountpath"></a>`mountPath` | [PublicPath](#publicpath) | yes | Public path where the mounted subtree should appear in the published site. |
| <a id="mountconfig-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | Short kind label that tells renderers and tooling what sort of mounted content this is. |
| <a id="mountconfig-trustclass"></a>`trustClass` | [TrustClass](#trustclass) | yes | Trust level for the mounted content, used by downstream tooling to decide how much confidence to place in its structure or metadata. |
| <a id="mountconfig-versionscope"></a>`versionScope` | [NonEmptyString](#nonemptystring) | no | Optional label describing which version context this mount belongs to, when the same component can expose several mounted trees. |
| <a id="mountconfig-indexbehavior"></a>`indexBehavior` | [IndexBehavior](#indexbehavior) | no | How the mounted subtree should participate in generated indexes, listings, or navigation structures. |
| <a id="mountconfig-ownership"></a>`ownership` | [NonEmptyString](#nonemptystring) | no | Logical owner label used in staged metadata to explain who is responsible for this mounted subtree. |
| <a id="mountconfig-metadata"></a>`metadata` | [ExtensionsObject](#extensionsobject) | no | Small JSON-like extension object for extra mount metadata that downstream tooling may consume. |

#### Selected field examples

- `source`: Example: `"generated/api"`
- `mountPath`: Example: `"/spark/api/"`
- `kind`: Example: `"generatedApi"`
- `versionScope`: Example: `"release"`
- `ownership`: Example: `"runtime-docs"`

<a id="namedrefconfig"></a>
### NamedRefConfig

Named source-control ref intentionally exposed as a stable version context.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="namedrefconfig-key"></a>`key` | [Identifier](#identifier) | yes | Stable identifier used elsewhere in the catalog to select this named ref. |
| <a id="namedrefconfig-ref"></a>`ref` | [RefString](#refstring) | yes | Exact source-control ref to resolve when this named context is selected. |
| <a id="namedrefconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable label shown in version pickers, breadcrumbs, or other rendered UI. |
| <a id="namedrefconfig-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Short maturity label that explains how stable or experimental this named ref should be treated. |
| <a id="namedrefconfig-description"></a>`description` | [NonEmptyString](#nonemptystring) | no | Human-readable explanation of what this named ref contains or who should use it. |

#### Selected field examples

- `key`: Example: `"preview"`
- `ref`: Example: `"refs/heads/preview"`
- `displayName`: Example: `"Preview"`
- `maturity`: Example: `"preview"`
- `description`: Example: `"Early access docs for the next planned minor release."`

<a id="originconfig"></a>
### OriginConfig

Named public base URL that published routes can resolve against.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="originconfig-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | Base public URL for this publication origin. |
| <a id="originconfig-canonical"></a>`canonical` | bool | no | Whether this origin should be treated as canonical when multiple origins publish the same target. |
| <a id="originconfig-labels"></a>`labels` | list[[NonEmptyString](#nonemptystring)] | no | Optional human-readable labels for renderer or deployment tooling. |

<a id="publicationconfig"></a>
### PublicationConfig

Resolved-or-authored route layout choices for a component or artifact.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationconfig-origin"></a>`origin` | [OriginKey](#originkey) | no | Publication origin key to use for this component or artifact. |
| <a id="publicationconfig-pathsegment"></a>`pathSegment` | [NonEmptyString](#nonemptystring) | no | Path segment appended below an inherited path prefix or mount root. |
| <a id="publicationconfig-mountpath"></a>`mountPath` | [PublicPath](#publicpath) | no | Explicit public root path for the component's published content. |
| <a id="publicationconfig-componentpath"></a>`componentPath` | [PublicPath](#publicpath) | no | Explicit public path for the component landing page or overview root. |
| <a id="publicationconfig-developmentpath"></a>`developmentPath` | [PublicPath](#publicpath) | no | Explicit public path for the moving latest/development docs surface. |
| <a id="publicationconfig-docspath"></a>`docsPath` | [PublicPath](#publicpath) | no | Explicit public docs landing path exposed to downstream consumers; defaults to the development/latest path unless an additional docs segment or override is configured. |
| <a id="publicationconfig-assetspath"></a>`assetsPath` | [PublicPath](#publicpath) | no | Explicit public path for static assets below the component root. |
| <a id="publicationconfig-canonicalpath"></a>`canonicalPath` | [PublicPath](#publicpath) | no | Optional canonical public path used when aliases or multiple origins are present. |
| <a id="publicationconfig-aliases"></a>`aliases` | list[[RouteAliasConfig](#routealiasconfig)] | no | Additional public aliases that should resolve to the same published target. |
| <a id="publicationconfig-redirects"></a>`redirects` | list[[RedirectRuleConfig](#redirectruleconfig)] | no | Redirect rules to emit for legacy or moved routes. |

#### Selected field examples

- `mountPath`: Example: `"/spark/"`

<a id="publicationselectionpolicy"></a>
### PublicationSelectionPolicy

Planning-time rule set for which version contexts are staged and linked.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationselectionpolicy-development"></a>`development` | bool | no | Whether to publish the moving development context represented by the artifact's `developmentRef`. |
| <a id="publicationselectionpolicy-lineheads"></a>`lineHeads` | [LineHeadSelectionPolicy](#lineheadselectionpolicy) | no | Rule for including release-line head contexts such as `4.0` or `3.5`. |
| <a id="publicationselectionpolicy-releases"></a>`releases` | [ReleaseSelectionPolicy](#releaseselectionpolicy) | no | Rule for including exact released-version contexts such as `4.0.1`. |
| <a id="publicationselectionpolicy-namedrefs"></a>`namedRefs` | list[[Identifier](#identifier)] | no | Named ref keys to include as publishable contexts in addition to development, line-head, or released versions. |
| <a id="publicationselectionpolicy-candidates"></a>`candidates` | [CandidateSelectionPolicy](#candidateselectionpolicy) | no | Rule for including release-candidate contexts when they should be visible to readers. |

#### Selected field examples

- `namedRefs`: Example: `["preview","stable"]`

<a id="redirectruleconfig"></a>
### RedirectRuleConfig

Redirect rule that sends one published path to another internal or external target.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="redirectruleconfig-frompath"></a>`fromPath` | [PublicPath](#publicpath) | yes | Public path that should redirect instead of serving its own content. |
| <a id="redirectruleconfig-fromorigin"></a>`fromOrigin` | [OriginKey](#originkey) | no | Optional origin override when the redirect should only exist on one named publication origin. |
| <a id="redirectruleconfig-target"></a>`target` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | yes | Destination of the redirect, either as a typed internal reference string or as a fully qualified external URL. |
| <a id="redirectruleconfig-status"></a>`status` | int | no | HTTP redirect status to emit; when omitted, downstream tooling applies its default redirect status. |
| <a id="redirectruleconfig-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | Short explanation of why the redirect exists, for example to describe a rename, consolidation, or withdrawn release route. |

#### Selected field examples

- `fromPath`: Example: `"/spark/docs/current/"`
- `fromOrigin`: Example: `"archive"`
- `target`: Example: `"route:/spark/latest/"`
- `status`: Example: `308`
- `reason`: Example: `"Current docs live on the latest release route."`

<a id="releaselineconfig"></a>
### ReleaseLineConfig

One logical release line, such as `4.0`, together with its lifecycle metadata.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselineconfig-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | Stable key for the release line, typically matching the family label used in URLs and navigation. |
| <a id="releaselineconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable label shown to readers when the raw line key is not ideal UI text. |
| <a id="releaselineconfig-parent"></a>`parent` | [NonEmptyString](#nonemptystring) | no | Optional parent release-line key used to model lineage such as `4.x` inheriting from `3.x` policy or navigation structure. |
| <a id="releaselineconfig-latest"></a>`latest` | [VersionString](#versionstring) | yes | Latest released version currently considered the head of this release line. |
| <a id="releaselineconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label that should be shown for the line as a whole. |
| <a id="releaselineconfig-aliases"></a>`aliases` | list[[NonEmptyString](#nonemptystring)] | no | Alternate labels that should also resolve to this release line in generated metadata or UI. |
| <a id="releaselineconfig-maintenanceref"></a>`maintenanceRef` | [RefString](#refstring) | no | Explicit maintenance branch ref for the line when it should not be derived from `maintenanceRefPattern`. |
| <a id="releaselineconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes that apply to the release line. |

#### Selected field examples

- `key`: Example: `"4.0"`
- `displayName`: Example: `"4.0 line"`
- `parent`: Example: `"3.5"`
- `latest`: Example: `"4.0.1"`
- `supportStatus`: Example: `"supported"`
- `aliases`: Example: `["stable"]`
- `maintenanceRef`: Example: `"refs/heads/release-4.0"`

<a id="releaseselectionpolicy"></a>
### ReleaseSelectionPolicy

Rule for which exact released versions should become published contexts.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaseselectionpolicy-mode"></a>`mode` | [ReleaseSelectionMode](#releaseselectionmode) | yes | Selection strategy for released versions, for example the latest `n` releases or one explicit version list. |
| <a id="releaseselectionpolicy-count"></a>`count` | [PositiveInteger](#positiveinteger) | no | How many most-recent releases to include when `mode` is `latestN`. |
| <a id="releaseselectionpolicy-versions"></a>`versions` | list[[VersionString](#versionstring)] | no | Exact released versions to include when `mode` is `explicit`. |

#### Selected field examples

- `count`: Example: `3`
- `versions`: Example: `["4.0.0","4.0.1"]`

<a id="routealiasconfig"></a>
### RouteAliasConfig

Additional public route that resolves to the same published destination.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="routealiasconfig-path"></a>`path` | [PublicPath](#publicpath) | yes | Alternate public path that should resolve to the same page family or landing target as the primary route. |
| <a id="routealiasconfig-origin"></a>`origin` | [OriginKey](#originkey) | no | Optional origin override when the alias should only exist on one named publication origin. |
| <a id="routealiasconfig-label"></a>`label` | [NonEmptyString](#nonemptystring) | no | Human-readable label that renderers can use when presenting this alias in navigation or metadata. |

#### Selected field examples

- `path`: Example: `"/spark/stable/"`
- `origin`: Example: `"archive"`
- `label`: Example: `"stable"`

<a id="sitecatalogdocumentv1"></a>
### SiteCatalogDocumentV1

Canonical site catalog that lists participating components, shared defaults, source bindings, publication origins, and publication policy for one site.

- category: `authored`
- ownership: `consumer-owned`
- file contract: `site/catalog.yaml`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sitecatalogdocumentv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the catalog format. |
| <a id="sitecatalogdocumentv1-defaults"></a>`defaults` | [CatalogDefaults](#catalogdefaults) | no | Shared default settings applied before per-component overrides. |
| <a id="sitecatalogdocumentv1-site"></a>`site` | [SiteContentConfig](#sitecontentconfig) | no | Consumer-owned top-level site pages, assets, and vendor-asset declarations. |
| <a id="sitecatalogdocumentv1-origins"></a>`origins` | dict[[OriginKey](#originkey), [OriginConfig](#originconfig)] | no | Named publication origins that components can target. |
| <a id="sitecatalogdocumentv1-sources"></a>`sources` | dict[[SourceKey](#sourcekey), [SourceConfig](#sourceconfig)] | no | Named repository or checkout bindings used by components and artifacts. |
| <a id="sitecatalogdocumentv1-groups"></a>`groups` | dict[[Identifier](#identifier), [GroupConfig](#groupconfig)] | no | Optional grouping defaults shared by multiple components. |
| <a id="sitecatalogdocumentv1-components"></a>`components` | list[[ComponentCatalogEntry](#componentcatalogentry)] | yes | Participating components in this consumer-authored catalog. |

#### Inheritance

Defaults flow from `defaults` to `groups` to individual component entries. See [component entries](#sitecatalogdocumentv1-components).

#### Example: Catalog with a single component, a single artifact, and release selection policy.

```yaml
schemaVersion: 1
defaults:
  docsRoot: docs
  publication:
    origin: docs
site: {}
origins:
  docs:
    baseUrl: https://docs.example.org
sources:
  runtime:
    localDir: components/runtime
components:
- slug: spark
  weight: 100
  content:
    source: runtime
  publication:
    mountPath: /spark/
  artifacts:
  - key: runtime
    source: runtime
    versioning:
      developmentRef: main
      tagPattern: ^v.*$
    publicationSelection:
      development: true
      lineHeads:
        mode: allAuthored
      releases:
        mode: latestPerLine
    lifecycle:
      releaseLines:
      - key: '4.0'
        latest: 4.0.0
        maintenanceRef: maintenance/4.0
      releases:
      - version: 4.0.0
```

<a id="sitecontentconfig"></a>
### SiteContentConfig

Top-level pages and asset trees that belong to the site as a whole.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sitecontentconfig-pagesroot"></a>`pagesRoot` | [RepoRelativePath](#reporelativepath) | no | Repository-relative root for consumer-owned top-level site pages. |
| <a id="sitecontentconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) | no | Repository-relative root for consumer-owned top-level static assets. |
| <a id="sitecontentconfig-vendorassets"></a>`vendorAssets` | list[TopLevelAssetConfig] | no | Additional imported asset trees mounted into the top-level site assets area. |

<a id="sourceconfig"></a>
### SourceConfig

Named repository or checkout binding reused by components and artifacts.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sourceconfig-localdir"></a>`localDir` | [RepoRelativePath](#reporelativepath) | yes | Workspace-relative checkout or source directory. |
| <a id="sourceconfig-repository"></a>`repository` | [UrlString](#urlstring) | no | Optional remote repository URL associated with this source. |
| <a id="sourceconfig-defaultbranch"></a>`defaultBranch` | [RefString](#refstring) | no | Optional default branch or ref for this source. |
| <a id="sourceconfig-metadatafile"></a>`metadataFile` | [RepoRelativePath](#reporelativepath) | no | Optional override for the component metadata file inside this source tree. |

<a id="supportstatusdefinition"></a>
### SupportStatusDefinition

One reusable support-status label, description, and default lifecycle behavior.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportstatusdefinition-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | yes | Human-readable status label shown to readers, such as `Supported` or `Security fixes only`. |
| <a id="supportstatusdefinition-order"></a>`order` | int | no | Optional sort order used when several support statuses should appear in a stable display order. |
| <a id="supportstatusdefinition-description"></a>`description` | [NonEmptyString](#nonemptystring) | no | Human-readable explanation of what this support status means in practice. |
| <a id="supportstatusdefinition-defaultmaintenancephase"></a>`defaultMaintenancePhase` | [NonEmptyString](#nonemptystring) | no | Default maintenance-phase label to apply when a release uses this support status and does not provide a more specific phase. |

#### Selected field examples

- `displayName`: Example: `"Supported"`
- `order`: Example: `10`
- `description`: Example: `"Receives regular fixes and new patch releases."`
- `defaultMaintenancePhase`: Example: `"active"`

<a id="supportwindow"></a>
### SupportWindow

Lifecycle dates and support notes for one release line or exact release.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportwindow-releasedate"></a>`releaseDate` | [TimestampString](#timestampstring) | no | Release date for the line or version that this support window describes. |
| <a id="supportwindow-maintenancephase"></a>`maintenancePhase` | [NonEmptyString](#nonemptystring) | no | Short label for the current maintenance phase, such as general availability, maintenance, or security-only support. |
| <a id="supportwindow-endofactivesupportdate"></a>`endOfActiveSupportDate` | [TimestampString](#timestampstring) | no | Date after which the release no longer receives full active support. |
| <a id="supportwindow-endofsupportdate"></a>`endOfSupportDate` | [TimestampString](#timestampstring) | no | Date after which the release is no longer supported in normal maintenance channels. |
| <a id="supportwindow-endoflifedate"></a>`endOfLifeDate` | [TimestampString](#timestampstring) | no | Final retirement date after which the release should be treated as fully end-of-life. |
| <a id="supportwindow-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) | no | Canonical URL that explains the support policy referenced by this support window. |
| <a id="supportwindow-notes"></a>`notes` | [NonEmptyString](#nonemptystring) | no | Additional notes that clarify exceptions, migration advice, or support caveats. |

#### Selected field examples

- `releaseDate`: Example: `"2026-04-01T00:00:00Z"`
- `maintenancePhase`: Example: `"security-fixes"`

## Provider input types

Normalized provider snapshot contracts consumed by the pipeline.

<a id="providerasset"></a>
### ProviderAsset

Downloadable asset attached to one provider release or candidate record.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerasset-name"></a>`name` | [NonEmptyString](#nonemptystring) | yes | Filename or display label of the downloadable asset. |
| <a id="providerasset-url"></a>`url` | [UrlString](#urlstring) | yes | Canonical download URL for the asset. |
| <a id="providerasset-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | no | Short asset kind label, for example `binary`, `source`, `signature`, or `sbom`. |
| <a id="providerasset-mediatype"></a>`mediaType` | [NonEmptyString](#nonemptystring) | no | Declared media type for the asset payload when the provider exposes it. |
| <a id="providerasset-size"></a>`size` | [NonNegativeInteger](#nonnegativeinteger) | no | Asset size in bytes when the provider exposes it. |
| <a id="providerasset-checksums"></a>`checksums` | dict[[Identifier](#identifier), [NonEmptyString](#nonemptystring)] | no | Checksum values keyed by algorithm name, such as `sha512` or `sha256`. |
| <a id="providerasset-signatureurl"></a>`signatureUrl` | [UrlString](#urlstring) | no | URL of the detached signature file, if available. |
| <a id="providerasset-sbomurl"></a>`sbomUrl` | [UrlString](#urlstring) | no | URL of the asset's software bill of materials, if available. |
| <a id="providerasset-provenanceurl"></a>`provenanceUrl` | [UrlString](#urlstring) | no | URL of provenance or attestation metadata associated with this asset, if available. |

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
| <a id="providerdescriptor-key"></a>`key` | [ProviderKey](#providerkey) | yes | Stable provider identifier referenced by every record emitted from this provider. |
| <a id="providerdescriptor-type"></a>`type` | [NonEmptyString](#nonemptystring) | yes | Provider implementation type, such as `github`, `git`, or another fetcher-specific backend name. |
| <a id="providerdescriptor-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable provider label shown in diagnostics or rendered metadata. |
| <a id="providerdescriptor-baseurl"></a>`baseUrl` | [ProviderBaseUrl](#providerbaseurl) | no | Base URL for the provider service when records can link back to a human-browsable origin. |
| <a id="providerdescriptor-fetchedat"></a>`fetchedAt` | [TimestampString](#timestampstring) | yes | Timestamp when this provider snapshot section was fetched or refreshed. |

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
| <a id="providerrecord-provider"></a>`provider` | [ProviderKey](#providerkey) | yes | Provider key that identifies which fetched provider emitted this record. |
| <a id="providerrecord-kind"></a>`kind` | [RecordKind](#recordkind) | yes | Record kind, such as exact release, release candidate, development ref, line head, or named ref. |
| <a id="providerrecord-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Component slug that this provider record belongs to. |
| <a id="providerrecord-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | Artifact key that this provider record belongs to. |
| <a id="providerrecord-sourcekey"></a>`sourceKey` | [SourceKey](#sourcekey) | no | Optional source binding key when the provider record came from one named catalog source. |
| <a id="providerrecord-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | Provider-specific stable identifier used to deduplicate and revisit the same upstream record. |
| <a id="providerrecord-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | Human-browsable upstream URL for the release, tag, or ref record. |
| <a id="providerrecord-version"></a>`version` | [VersionString](#versionstring) | no | Exact version string for release and candidate records when the provider exposes one. |
| <a id="providerrecord-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | Human-readable version label when the raw version string needs a friendlier presentation. |
| <a id="providerrecord-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | Exact provider tag associated with this record when tags are available. |
| <a id="providerrecord-ref"></a>`ref` | [RefString](#refstring) | no | Exact source-control ref associated with this record, especially for development, line-head, or named-ref contexts. |
| <a id="providerrecord-commitsha"></a>`commitSha` | [NonEmptyString](#nonemptystring) | no | Resolved commit SHA for the record when the provider exposes it. |
| <a id="providerrecord-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) | no | Catalog-authored named-ref key that this provider record enriches when the record represents a named ref. |
| <a id="providerrecord-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key that groups this record with related versions such as `4.0`. |
| <a id="providerrecord-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](#nonemptystring)] | no | Ancestor release-line keys, ordered from nearest to farthest, used when lineage matters to selection or rendering. |
| <a id="providerrecord-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label associated with this record. |
| <a id="providerrecord-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | Publication state for the record, such as published, withdrawn, or tombstoned. |
| <a id="providerrecord-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Maturity label such as preview, beta, or stable that readers can use to judge readiness. |
| <a id="providerrecord-candidatesequence"></a>`candidateSequence` | [NonNegativeInteger](#nonnegativeinteger) | no | Numeric ordering hint for release candidates, usually the `rc` sequence number. |
| <a id="providerrecord-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | Vote status label for a candidate release when the provider exposes release-vote state. |
| <a id="providerrecord-createdat"></a>`createdAt` | [TimestampString](#timestampstring) | no | Timestamp when the upstream record was first created. |
| <a id="providerrecord-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | Timestamp when the upstream record became publicly available. |
| <a id="providerrecord-updatedat"></a>`updatedAt` | [TimestampString](#timestampstring) | no | Timestamp of the most recent upstream update observed for this record. |
| <a id="providerrecord-urls"></a>`urls` | dict[[NonEmptyString](#nonemptystring), [UrlString](#urlstring)] | no | Additional named URLs related to the record, such as notes, signatures, vote threads, or changelogs. |
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

## Planning and stage-contract types

Pipeline-emitted planning, diagnostics, and stage-manifest contracts.

<a id="checkreportv1"></a>
### CheckReportV1

Machine-readable result of `site-pipeline check`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checkreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the check report. |
| <a id="checkreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | Timestamp when the check report was generated. |
| <a id="checkreportv1-command"></a>`command` | Literal['check'] | yes | Command name that produced this report; always `check` for this contract. |
| <a id="checkreportv1-summary"></a>`summary` | [CheckSummary](#checksummary) | yes | Outcome summary with pass/fail state and diagnostic counts for the run. |
| <a id="checkreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | Structured diagnostics emitted during the check run. |

#### Example: Validation report with one warning that does not fail the run.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-04-06T08:35:00Z",
  "command": "check",
  "summary": {
    "status": "warnings",
    "passed": true,
    "failOnSeverity": "error",
    "errorCount": 0,
    "warningCount": 1,
    "infoCount": 0
  },
  "diagnostics": [
    {
      "severity": "warning",
      "code": "catalog.redirectReasonMissing",
      "message": "Redirect /spark/docs/current/ has no reader-facing reason.",
      "componentSlug": "spark",
      "targetId": "/spark/docs/current/"
    }
  ]
}
```

<a id="checksummary"></a>
### CheckSummary

Outcome counts and pass/fail decision for one `check` run.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checksummary-status"></a>`status` | [RunStatus](#runstatus) | yes | Overall diagnostic status for the run after counts were evaluated. |
| <a id="checksummary-passed"></a>`passed` | bool | yes | Whether the check run satisfied the configured failure threshold and should be treated as passing. |
| <a id="checksummary-failonseverity"></a>`failOnSeverity` | [CheckFailureThreshold](#checkfailurethreshold) | yes | Configured severity threshold that decides whether warnings already fail the run or only errors do. |
| <a id="checksummary-errorcount"></a>`errorCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | Number of error diagnostics emitted during the run. |
| <a id="checksummary-warningcount"></a>`warningCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | Number of warning diagnostics emitted during the run. |
| <a id="checksummary-infocount"></a>`infoCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | Number of informational diagnostics emitted during the run. |

<a id="pipelinediagnosticentry"></a>
### PipelineDiagnosticEntry

Structured diagnostic emitted during planning, checking, or staging.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinediagnosticentry-severity"></a>`severity` | [DiagnosticSeverity](#diagnosticseverity) | yes | Diagnostic severity level that callers can use for gating and presentation. |
| <a id="pipelinediagnosticentry-code"></a>`code` | [NonEmptyString](#nonemptystring) | yes | Stable machine-readable diagnostic code. |
| <a id="pipelinediagnosticentry-message"></a>`message` | [NonEmptyString](#nonemptystring) | yes | Primary human-readable diagnostic message. |
| <a id="pipelinediagnosticentry-componentslug"></a>`componentSlug` | [NonEmptyString](#nonemptystring) | no | Component slug associated with the diagnostic when a specific component is directly affected. |
| <a id="pipelinediagnosticentry-artifactkey"></a>`artifactKey` | [NonEmptyString](#nonemptystring) | no | Artifact key associated with the diagnostic when a specific artifact is directly affected. |
| <a id="pipelinediagnosticentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | no | Additional target identifier, such as a path, ref, or release key, that helps callers locate the problem precisely. |
| <a id="pipelinediagnosticentry-details"></a>`details` | [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) \| [ExtensionsObject](#extensionsobject) | no | Structured detail payload for the diagnostic, or a bounded summary when the original detail payload was too large. |

#### Selected field examples

- `code`: Example: `"catalog.invalidRedirectTarget"`
- `message`: Example: `"Redirect target route:/spark/missing/ could not be resolved."`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `targetId`: Example: `"/spark/docs/current/"`

<a id="reduceddiagnosticdetailssummary"></a>
### ReducedDiagnosticDetailsSummary

Compact placeholder used when full diagnostic details were too large to keep.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="reduceddiagnosticdetailssummary-omitted"></a>`omitted` | Literal[True] | yes | Always `true`, signalling that the original diagnostic details were intentionally omitted. |
| <a id="reduceddiagnosticdetailssummary-reason"></a>`reason` | Literal['sizeLimitExceeded'] | yes | Reason why the original diagnostic details were replaced by this bounded summary. |
| <a id="reduceddiagnosticdetailssummary-actualbytes"></a>`actualBytes` | [PositiveInteger](#positiveinteger) | yes | Actual serialized size of the original diagnostic details payload in bytes. |
| <a id="reduceddiagnosticdetailssummary-limitbytes"></a>`limitBytes` | [PositiveInteger](#positiveinteger) | yes | Configured byte limit that the original diagnostic details exceeded. |
| <a id="reduceddiagnosticdetailssummary-summary"></a>`summary` | [NonEmptyString](#nonemptystring) | no | Short human-readable summary of the omitted details payload. |
| <a id="reduceddiagnosticdetailssummary-fingerprint"></a>`fingerprint` | [NonEmptyString](#nonemptystring) | no | Stable fingerprint that lets tooling correlate repeated oversized payloads without storing the full payload. |

#### Selected field examples

- `actualBytes`: Example: `524288`
- `limitBytes`: Example: `65536`

<a id="resolvedmaterializationentry"></a>
### ResolvedMaterializationEntry

One local checkout or fetched input that the planner expects to exist.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationentry-sourcekey"></a>`sourceKey` | [NonEmptyString](#nonemptystring) | no | Named source binding that produced this materialization requirement. |
| <a id="resolvedmaterializationentry-inputkind"></a>`inputKind` | [MaterializationInputKind](#materializationinputkind) | yes | Kind of materialized input, such as a component checkout, artifact checkout, or provider-derived fetch target. |
| <a id="resolvedmaterializationentry-componentslug"></a>`componentSlug` | [NonEmptyString](#nonemptystring) | no | Component slug for the materialized input when the requirement is tied to a specific component. |
| <a id="resolvedmaterializationentry-artifactkey"></a>`artifactKey` | [NonEmptyString](#nonemptystring) | no | Artifact key for the materialized input when the requirement is tied to one independently versioned artifact. |
| <a id="resolvedmaterializationentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key when the required local input is scoped to one maintenance line. |
| <a id="resolvedmaterializationentry-version"></a>`version` | [NonEmptyString](#nonemptystring) | no | Exact version when the required local input is scoped to one released version. |
| <a id="resolvedmaterializationentry-ref"></a>`ref` | [NonEmptyString](#nonemptystring) | no | Exact source-control ref when the planner resolved this input from a branch or named ref. |
| <a id="resolvedmaterializationentry-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | Exact tag name when the planner resolved this input from a tagged release. |
| <a id="resolvedmaterializationentry-commitsha"></a>`commitSha` | [NonEmptyString](#nonemptystring) | no | Resolved commit SHA for the required input when one was discovered. |
| <a id="resolvedmaterializationentry-expectedlocalpath"></a>`expectedLocalPath` | [LocalPathString](#localpathstring) | yes | Local filesystem path where the planner expects this input to be present or materialized. |
| <a id="resolvedmaterializationentry-status"></a>`status` | [MaterializationStatus](#materializationstatus) | yes | Current materialization status, such as already present, missing, or needing refresh. |
| <a id="resolvedmaterializationentry-provenance"></a>`provenance` | [NonEmptyString](#nonemptystring) | no | Short explanation of how the planner derived this materialization requirement. |
| <a id="resolvedmaterializationentry-watcheligible"></a>`watchEligible` | bool | no | Whether watch mode can safely monitor this input for incremental restaging. |
| <a id="resolvedmaterializationentry-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | Human-readable explanation of why this input is required or why its current status matters. |

#### Selected field examples

- `sourceKey`: Example: `"apache-spark"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`
- `releaseLine`: Example: `"4.0"`
- `version`: Example: `"4.0.0"`
- `ref`: Example: `"refs/heads/main"`
- `tag`: Example: `"v4.0.0"`
- `commitSha`: Example: `"6f0fd1f7b2c4a6d8e9f00123456789abcdef0123"`
- `expectedLocalPath`: Example: `".buildish/materialized/apache-spark/main"`

<a id="resolvedmaterializationreportv1"></a>
### ResolvedMaterializationReportV1

Machine-readable planning report for required local inputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the materialization planning report. |
| <a id="resolvedmaterializationreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | Timestamp when this planning report was generated. |
| <a id="resolvedmaterializationreportv1-target"></a>`target` | [PlanningTarget](#planningtarget) | yes | Planning target that this report was generated for, such as build or watch preparation. |
| <a id="resolvedmaterializationreportv1-entries"></a>`entries` | list[[ResolvedMaterializationEntry](#resolvedmaterializationentry)] | yes | Required local inputs together with their expected locations and current materialization status. |
| <a id="resolvedmaterializationreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | no | Structured diagnostics emitted while resolving required local inputs for this planning target. |

#### Example: Planning report with one required release checkout.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-04-06T08:30:00Z",
  "target": "build",
  "entries": [
    {
      "sourceKey": "apache-spark",
      "inputKind": "released",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "version": "4.0.0",
      "tag": "v4.0.0",
      "expectedLocalPath": ".buildish/materialized/apache-spark/v4.0.0",
      "status": "present",
      "watchEligible": false,
      "reason": "Release docs are staged from the release tag checkout."
    }
  ],
  "diagnostics": []
}
```

<a id="stagedatafiles"></a>
### StageDataFiles

Stage-relative paths of aggregate metadata files currently present in one stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedatafiles-components"></a>`components` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative path of the published component aggregate file. |
| <a id="stagedatafiles-artifacts"></a>`artifacts` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative path of the published artifact aggregate file. |
| <a id="stagedatafiles-routes"></a>`routes` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative path of the published route aggregate file. |
| <a id="stagedatafiles-redirects"></a>`redirects` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative path of the published redirect aggregate file. |
| <a id="stagedatafiles-releases"></a>`releases` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the published release aggregate file when release metadata is present. |
| <a id="stagedatafiles-candidates"></a>`candidates` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the published candidate aggregate file when release-candidate metadata is present. |
| <a id="stagedatafiles-refs"></a>`refs` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the published ref aggregate file when development, line-head, or named-ref metadata is present. |
| <a id="stagedatafiles-translations"></a>`translations` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the published translation aggregate file when localized page groups are present. |
| <a id="stagedatafiles-compatibility"></a>`compatibility` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the published compatibility aggregate file when compatibility assertions are present. |
| <a id="stagedatafiles-mounts"></a>`mounts` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the published mount aggregate file when mounted subtrees are present. |
| <a id="stagedatafiles-providers"></a>`providers` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the provider aggregate file when provider metadata is present in the stage. |
| <a id="stagedatafiles-contentindex"></a>`contentIndex` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the content-index aggregate file when the stage includes a generated page index. |
| <a id="stagedatafiles-diagnostics"></a>`diagnostics` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the diagnostics aggregate file when diagnostics were published into the stage. |
| <a id="stagedatafiles-unitcontributions"></a>`unitContributions` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the persisted unit-contribution manifest file when it is present. |
| <a id="stagedatafiles-outputownership"></a>`outputOwnership` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the output-ownership map when incremental rebuild metadata is present. |
| <a id="stagedatafiles-aggregatedependencies"></a>`aggregateDependencies` | [StageRelativePath](#stagerelativepath) | no | Stage-relative path of the aggregate-dependency map when incremental rebuild metadata is present. |

#### Selected field examples

- `components`: Example: `"data/components.json"`
- `artifacts`: Example: `"data/artifacts.json"`
- `routes`: Example: `"data/routes.json"`
- `redirects`: Example: `"data/redirects.json"`
- `releases`: Example: `"data/releases.json"`
- `candidates`: Example: `"data/candidates.json"`
- `refs`: Example: `"data/refs.json"`
- `translations`: Example: `"data/translations.json"`
- `compatibility`: Example: `"data/compatibility.json"`
- `mounts`: Example: `"data/mounts.json"`
- `providers`: Example: `"data/providers.json"`
- `contentIndex`: Example: `"data/content-index.json"`
- `diagnostics`: Example: `"data/diagnostics.json"`
- `unitContributions`: Example: `"data/unit-contributions.json"`
- `outputOwnership`: Example: `"data/output-ownership.json"`
- `aggregateDependencies`: Example: `"data/aggregate-dependencies.json"`

<a id="stagemanifestv1"></a>
### StageManifestV1

Authoritative entry-point document for a staged output tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `manifest.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagemanifestv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the stage manifest. |
| <a id="stagemanifestv1-stagelayoutversion"></a>`stageLayoutVersion` | [SchemaVersion](#schemaversion) | yes | Version of the stage directory layout contract that this manifest follows. |
| <a id="stagemanifestv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | Timestamp when the manifest was generated. |
| <a id="stagemanifestv1-command"></a>`command` | [StageCommand](#stagecommand) | yes | Stage-producing command that created the stage tree represented by this manifest. |
| <a id="stagemanifestv1-frontmatterformat"></a>`frontMatterFormat` | Literal['yaml'] | yes | Front matter serialization format used for staged content files. |
| <a id="stagemanifestv1-aggregateformat"></a>`aggregateFormat` | Literal['json'] | yes | Serialization format used for aggregate metadata files in the stage data directory. |
| <a id="stagemanifestv1-roots"></a>`roots` | [StageRoots](#stageroots) | yes | Top-level stage directories used for content, static assets, and aggregate data. |
| <a id="stagemanifestv1-datafiles"></a>`dataFiles` | [StageDataFiles](#stagedatafiles) | yes | Stage-relative paths of aggregate metadata files currently present in the stage. |

#### Example: Stage manifest that points at content, static, and aggregate roots.

```json
{
  "schemaVersion": 1,
  "stageLayoutVersion": 1,
  "generatedAt": "2026-04-06T08:40:00Z",
  "command": "build",
  "frontMatterFormat": "yaml",
  "aggregateFormat": "json",
  "roots": {
    "content": "content",
    "static": "static",
    "data": "data"
  },
  "dataFiles": {
    "components": "data/components.json",
    "artifacts": "data/artifacts.json",
    "routes": "data/routes.json",
    "redirects": "data/redirects.json",
    "releases": "data/releases.json",
    "refs": "data/refs.json",
    "contentIndex": "data/content-index.json"
  }
}
```

<a id="stageroots"></a>
### StageRoots

Named top-level directories inside a stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stageroots-content"></a>`content` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative directory that contains rendered pages and content files. |
| <a id="stageroots-static"></a>`static` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative directory that contains copied static assets. |
| <a id="stageroots-data"></a>`data` | [StageRelativePath](#stagerelativepath) | yes | Stage-relative directory that contains aggregate metadata files. |

#### Selected field examples

- `content`: Example: `"content"`
- `static`: Example: `"static"`
- `data`: Example: `"data"`

<a id="stagerunreportv1"></a>
### StageRunReportV1

Machine-readable result of `build` or one completed watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the stage run report. |
| <a id="stagerunreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | Timestamp when the stage run report was generated. |
| <a id="stagerunreportv1-command"></a>`command` | [StageCommand](#stagecommand) | yes | Stage-producing command that produced this report, such as `build` or `watch`. |
| <a id="stagerunreportv1-summary"></a>`summary` | [StageRunSummary](#stagerunsummary) | yes | Outcome summary with success state, stage usability, and diagnostic counts for the run. |
| <a id="stagerunreportv1-stagerootpath"></a>`stageRootPath` | [LocalPathString](#localpathstring) | no | Local path to the root of the stage tree, if the run produced one. |
| <a id="stagerunreportv1-manifestpath"></a>`manifestPath` | [LocalPathString](#localpathstring) | no | Local path to the generated stage manifest when the stage is usable. |
| <a id="stagerunreportv1-cycle"></a>`cycle` | [NonNegativeInteger](#nonnegativeinteger) | no | Completed watch-cycle number for watch reports; omitted for one-shot build reports. |
| <a id="stagerunreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | Structured diagnostics emitted during the stage-producing run. |

#### Selected field examples

- `cycle`: Example: `3`

#### Example: Successful build report with a usable stage manifest.

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-04-06T08:40:00Z",
  "command": "build",
  "summary": {
    "status": "clean",
    "succeeded": true,
    "wroteStage": true,
    "stageUsable": true,
    "errorCount": 0,
    "warningCount": 0,
    "infoCount": 2
  },
  "stageRootPath": ".buildish/stage/current",
  "manifestPath": ".buildish/stage/current/manifest.json",
  "diagnostics": []
}
```

<a id="stagerunsummary"></a>
### StageRunSummary

Outcome counts and usability flags for one stage-producing run or watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunsummary-status"></a>`status` | [RunStatus](#runstatus) | yes | Overall diagnostic status for the run after counts were evaluated. |
| <a id="stagerunsummary-succeeded"></a>`succeeded` | bool | yes | Whether the run finished with a usable stage and should be treated as successful. |
| <a id="stagerunsummary-wrotestage"></a>`wroteStage` | bool | yes | Whether the run actually wrote or refreshed stage output on disk. |
| <a id="stagerunsummary-stageusable"></a>`stageUsable` | bool | yes | Whether downstream tooling may safely use the stage after this run finished. |
| <a id="stagerunsummary-errorcount"></a>`errorCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | Number of error diagnostics emitted during the run. |
| <a id="stagerunsummary-warningcount"></a>`warningCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | Number of warning diagnostics emitted during the run. |
| <a id="stagerunsummary-infocount"></a>`infoCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | Number of informational diagnostics emitted during the run. |

## Staged front matter types

Front matter and page-level metadata emitted into staged content.

<a id="artifactfrontmattersummary"></a>
### ArtifactFrontMatterSummary

Small artifact summary embedded in component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactfrontmattersummary-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | Artifact key used to identify the artifact in page links and typed references. |
| <a id="artifactfrontmattersummary-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable artifact label shown in page chrome or listings. |
| <a id="artifactfrontmattersummary-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | Most recent stable version that readers should treat as the default recommendation. |
| <a id="artifactfrontmattersummary-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] | no | Compact release-line summaries that the page can use for navigation or version selection. |

#### Selected field examples

- `key`: Example: `"runtime"`
- `displayName`: Example: `"Runtime"`
- `latestStable`: Example: `"4.0.1"`

<a id="pipelinecomponentfrontmatter"></a>
### PipelineComponentFrontMatter

Component-level pipeline metadata injected into staged page front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinecomponentfrontmatter-slug"></a>`slug` | [Slug](#slug) | yes | Stable component slug for the owning component. |
| <a id="pipelinecomponentfrontmatter-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable component name shown in page chrome or navigation. |
| <a id="pipelinecomponentfrontmatter-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | Resolved publication roots and URLs for the owning component. |
| <a id="pipelinecomponentfrontmatter-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] | no | Compact artifact summaries that pages can use for version navigation or page chrome. |

#### Selected field examples

- `slug`: Example: `"spark"`
- `displayName`: Example: `"Apache Spark"`

<a id="pipelinefrontmatternamespace"></a>
### PipelineFrontMatterNamespace

Reserved top-level front matter namespace that the pipeline injects into staged pages.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinefrontmatternamespace-component"></a>`component` | [PipelineComponentFrontMatter](#pipelinecomponentfrontmatter) | no | Component-level pipeline metadata injected into the staged page. |
| <a id="pipelinefrontmatternamespace-page"></a>`page` | [PipelinePageFrontMatter](#pipelinepagefrontmatter) | no | Page-local pipeline metadata injected into the staged page. |

#### Example: Injected front matter for a component page and a released version.

```yaml
component:
  slug: spark
  displayName: Apache Spark
  publication:
    origin:
      key: archive
      baseUrl: https://archive.apache.org/dist/spark
      hostname: archive.apache.org
    paths:
      component: /spark/
      development: /spark/main/
      docs: /spark/docs/
      assets: /spark/assets/
    urls:
      component: https://archive.apache.org/dist/spark/
      development: https://archive.apache.org/dist/spark/main/
      docs: https://archive.apache.org/dist/spark/docs/
      assets: https://archive.apache.org/dist/spark/assets/
page:
  kind: docsPage
  section: documentation
  artifactKey: runtime
  path: /spark/4.0.0/docs/getting-started/
  url: https://archive.apache.org/dist/spark/4.0.0/docs/getting-started/
  componentPath: /spark/
  componentUrl: https://archive.apache.org/dist/spark/
  version:
    kind: released
    label: 4.0.0
    tag: v4.0.0
```

<a id="pipelinepagefrontmatter"></a>
### PipelinePageFrontMatter

Page-local pipeline metadata injected into staged page front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinepagefrontmatter-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | Short page kind label used by renderers to distinguish landing pages, docs pages, release notes, and similar page families. |
| <a id="pipelinepagefrontmatter-section"></a>`section` | [NonEmptyString](#nonemptystring) | no | Optional higher-level section label that groups the page with related navigation or templates. |
| <a id="pipelinepagefrontmatter-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | Artifact key when the page belongs to one independently versioned artifact. |
| <a id="pipelinepagefrontmatter-path"></a>`path` | [PublicPath](#publicpath) | yes | Published public path for this page. |
| <a id="pipelinepagefrontmatter-url"></a>`url` | [UrlString](#urlstring) | yes | Canonical absolute URL for this page. |
| <a id="pipelinepagefrontmatter-canonicalurl"></a>`canonicalUrl` | [UrlString](#urlstring) | no | Explicit canonical URL when it should differ from `url`, for example to consolidate duplicate routes. |
| <a id="pipelinepagefrontmatter-alternateurls"></a>`alternateUrls` | list[[UrlString](#urlstring)] | no | Additional absolute URLs that should be considered alternate entry points for the same page. |
| <a id="pipelinepagefrontmatter-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | no | Locale key for this page when it participates in localization. |
| <a id="pipelinepagefrontmatter-defaultlocale"></a>`defaultLocale` | bool | no | Whether this page represents the default locale within its translation group. |
| <a id="pipelinepagefrontmatter-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | no | Shared key that ties translated sibling pages together across locales. |
| <a id="pipelinepagefrontmatter-translations"></a>`translations` | list[[TranslationLinkSummary](#translationlinksummary)] | no | Compact links to translated sibling pages in other locales. |
| <a id="pipelinepagefrontmatter-componentpath"></a>`componentPath` | [PublicPath](#publicpath) | yes | Public root path for the owning component. |
| <a id="pipelinepagefrontmatter-componenturl"></a>`componentUrl` | [UrlString](#urlstring) | yes | Absolute URL for the owning component root. |
| <a id="pipelinepagefrontmatter-version"></a>`version` | [VersionContext](#versioncontext) | no | Version or ref context attached when this page belongs to a versioned route set. |
| <a id="pipelinepagefrontmatter-provider"></a>`provider` | [ProviderProvenance](#providerprovenance) | no | Pointer back to the upstream provider record that informed the page's version metadata. |

#### Selected field examples

- `kind`: Example: `"docsPage"`
- `section`: Example: `"documentation"`
- `artifactKey`: Example: `"runtime"`
- `path`: Example: `"/spark/4.0.0/docs/getting-started/"`
- `locale`: Example: `"en"`
- `translationKey`: Example: `"spark-overview"`
- `componentPath`: Example: `"/spark/"`

<a id="providerprovenance"></a>
### ProviderProvenance

Small pointer back to the provider record that informed this page's version.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerprovenance-key"></a>`key` | [ProviderKey](#providerkey) | yes | Provider key for the upstream system that supplied the current version metadata. |
| <a id="providerprovenance-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | Provider-specific stable identifier for the upstream record that informed this page. |
| <a id="providerprovenance-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | Human-browsable URL for the upstream record that informed this page. |

#### Selected field examples

- `key`: Example: `"github-releases"`
- `externalId`: Example: `"github:release:runtime-4.0.0"`

<a id="releaselinecontext"></a>
### ReleaseLineContext

Release-line context attached to one staged page's current version.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselinecontext-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | Release-line key for this page's version context. |
| <a id="releaselinecontext-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label associated with the current release line. |
| <a id="releaselinecontext-ancestors"></a>`ancestors` | list[[NonEmptyString](#nonemptystring)] | no | Ancestor release-line keys ordered from nearest to farthest. |
| <a id="releaselinecontext-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes attached to the current release line. |

#### Selected field examples

- `key`: Example: `"4.0"`
- `supportStatus`: Example: `"supported"`
- `ancestors`: Example: `["4.x","stable"]`

<a id="releaselinesummary"></a>
### ReleaseLineSummary

Small release-line summary embedded into page or component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselinesummary-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | Release-line key, such as `4.0`, for the summarized line. |
| <a id="releaselinesummary-parent"></a>`parent` | [NonEmptyString](#nonemptystring) | no | Optional parent release-line key when lineage should be preserved in front matter. |
| <a id="releaselinesummary-latest"></a>`latest` | [VersionString](#versionstring) | no | Latest released version currently associated with this line. |
| <a id="releaselinesummary-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label for the release line. |
| <a id="releaselinesummary-headref"></a>`headRef` | [RefString](#refstring) | no | Maintenance or line-head ref associated with this release line, if known. |
| <a id="releaselinesummary-aliases"></a>`aliases` | list[[NonEmptyString](#nonemptystring)] | no | Alternate labels that should also refer to this release line. |
| <a id="releaselinesummary-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes for the release line. |

#### Selected field examples

- `key`: Example: `"4.0"`
- `parent`: Example: `"4.x"`
- `latest`: Example: `"4.0.1"`
- `supportStatus`: Example: `"supported"`
- `headRef`: Example: `"refs/heads/release-4.0"`
- `aliases`: Example: `["stable"]`

<a id="resolvedorigin"></a>
### ResolvedOrigin

Resolved origin details for the current publication target.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedorigin-key"></a>`key` | [OriginKey](#originkey) | yes | Origin key selected for this published route or page. |
| <a id="resolvedorigin-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | Fully qualified base URL for the selected origin. |
| <a id="resolvedorigin-hostname"></a>`hostname` | [HostnameString](#hostnamestring) | yes | Hostname extracted from `baseUrl` for callers that need it without reparsing the URL. |

#### Selected field examples

- `key`: Example: `"archive"`
- `baseUrl`: Example: `"https://archive.apache.org/dist/spark"`
- `hostname`: Example: `"archive.apache.org"`

<a id="resolvedpathset"></a>
### ResolvedPathSet

Resolved public path roots for a component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedpathset-component"></a>`component` | [PublicPath](#publicpath) | yes | Public root path for the component as a whole. |
| <a id="resolvedpathset-development"></a>`development` | [PublicPath](#publicpath) | yes | Public root path for development-version content. |
| <a id="resolvedpathset-docs"></a>`docs` | [PublicPath](#publicpath) | yes | Public root path for versioned documentation content. |
| <a id="resolvedpathset-assets"></a>`assets` | [PublicPath](#publicpath) | yes | Public root path for shared component assets. |

#### Selected field examples

- `component`: Example: `"/spark/"`
- `development`: Example: `"/spark/main/"`
- `docs`: Example: `"/spark/docs/"`
- `assets`: Example: `"/spark/assets/"`

<a id="resolvedpublication"></a>
### ResolvedPublication

Resolved origin, path roots, and absolute URLs for a component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedpublication-origin"></a>`origin` | [ResolvedOrigin](#resolvedorigin) | yes | Origin details used to resolve paths into absolute URLs. |
| <a id="resolvedpublication-paths"></a>`paths` | [ResolvedPathSet](#resolvedpathset) | yes | Resolved public path roots for the component. |
| <a id="resolvedpublication-urls"></a>`urls` | [ResolvedUrlSet](#resolvedurlset) | yes | Resolved absolute URLs for the same publication roots. |

<a id="resolvedurlset"></a>
### ResolvedUrlSet

Resolved absolute URLs for a component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedurlset-component"></a>`component` | [UrlString](#urlstring) | yes | Absolute URL for the component root. |
| <a id="resolvedurlset-development"></a>`development` | [UrlString](#urlstring) | yes | Absolute URL for the development-version root. |
| <a id="resolvedurlset-docs"></a>`docs` | [UrlString](#urlstring) | yes | Absolute URL for the versioned docs root. |
| <a id="resolvedurlset-assets"></a>`assets` | [UrlString](#urlstring) | yes | Absolute URL for the shared component asset root. |

#### Selected field examples

- `component`: Example: `"https://archive.apache.org/dist/spark/"`
- `development`: Example: `"https://archive.apache.org/dist/spark/main/"`
- `docs`: Example: `"https://archive.apache.org/dist/spark/docs/"`
- `assets`: Example: `"https://archive.apache.org/dist/spark/assets/"`

<a id="translationlinksummary"></a>
### TranslationLinkSummary

Compact link to one translated sibling page.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="translationlinksummary-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | yes | Locale key for the translated sibling page. |
| <a id="translationlinksummary-path"></a>`path` | [PublicPath](#publicpath) | no | Public path for the translated sibling page, if available. |
| <a id="translationlinksummary-url"></a>`url` | [UrlString](#urlstring) | yes | Absolute URL for the translated sibling page. |
| <a id="translationlinksummary-title"></a>`title` | [NonEmptyString](#nonemptystring) | no | Localized page title for the translated sibling page. |

#### Selected field examples

- `locale`: Example: `"de"`
- `path`: Example: `"/de/spark/overview/"`
- `title`: Example: `"\u00dcbersicht"`

<a id="versioncontext"></a>
### VersionContext

Version, release-candidate, or ref context attached to one staged page.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="versioncontext-kind"></a>`kind` | [RecordKind](#recordkind) | yes | Kind of version context attached to the page, such as release, candidate, development ref, or named ref. |
| <a id="versioncontext-label"></a>`label` | [NonEmptyString](#nonemptystring) | yes | Primary label shown to readers for this version context. |
| <a id="versioncontext-path"></a>`path` | [PublicPath](#publicpath) | no | Public route root for this version context when it has a routable landing path. |
| <a id="versioncontext-url"></a>`url` | [UrlString](#urlstring) | no | Absolute URL for the version-context route root when it has one. |
| <a id="versioncontext-docspath"></a>`docsPath` | [PublicPath](#publicpath) | no | Public docs root for this version context when versioned docs are available. |
| <a id="versioncontext-docsurl"></a>`docsUrl` | [UrlString](#urlstring) | no | Absolute URL for the version-context docs root when it has one. |
| <a id="versioncontext-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | Exact tag name associated with this version context, if present. |
| <a id="versioncontext-ref"></a>`ref` | [RefString](#refstring) | no | Exact source-control ref associated with this version context, if present. |
| <a id="versioncontext-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) | no | Catalog-authored named-ref key when this context represents a named ref. |
| <a id="versioncontext-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | Publication-state label for this version context, such as published or withdrawn. |
| <a id="versioncontext-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Maturity label such as preview, beta, or stable. |
| <a id="versioncontext-candidatesequence"></a>`candidateSequence` | int | no | Release-candidate sequence number when this version context represents a candidate release. |
| <a id="versioncontext-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | Vote status label for release-candidate contexts when it is known. |
| <a id="versioncontext-releaseline"></a>`releaseLine` | [ReleaseLineContext](#releaselinecontext) | no | Release-line context attached to the current version when the version belongs to a known release line. |
| <a id="versioncontext-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes attached directly to this version context. |

#### Selected field examples

- `label`: Example: `"4.0.0"`
- `path`: Example: `"/spark/4.0.0/"`
- `docsPath`: Example: `"/spark/4.0.0/docs/"`
- `tag`: Example: `"v4.0.0"`
- `ref`: Example: `"refs/heads/main"`
- `namedRefKey`: Example: `"preview"`
- `maturity`: Example: `"stable"`
- `candidateSequence`: Example: `1`
- `voteStatus`: Example: `"passed"`

## Staged aggregate metadata types

Public aggregate JSON contracts emitted under `data/`.

<a id="artifactsdataentry"></a>
### ArtifactsDataEntry

Entry in `data/artifacts.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactsdataentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the artifact. |
| <a id="artifactsdataentry-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | Stable artifact key used by routes, aggregates, and typed references. |
| <a id="artifactsdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable artifact label shown in navigation and metadata. |
| <a id="artifactsdataentry-sourcekey"></a>`sourceKey` | [SourceKey](#sourcekey) | no | Named source binding that owns the artifact's docs and assets. |
| <a id="artifactsdataentry-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) | no | Repository-relative docs root for the artifact when it differs from the component default. |
| <a id="artifactsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](#providerkey)] | no | Provider keys that contributed version metadata for this artifact. |
| <a id="artifactsdataentry-versioning"></a>`versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | no | Version-discovery rules that explain how development refs, tags, and named refs are derived for the artifact. |
| <a id="artifactsdataentry-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | Most recent stable version recommended for readers. |
| <a id="artifactsdataentry-latestrelease"></a>`latestRelease` | [LatestReleaseSummary](#latestreleasesummary) | no | Compact summary of the latest known release for the artifact. |
| <a id="artifactsdataentry-latestcandidate"></a>`latestCandidate` | [LatestCandidateSummary](#latestcandidatesummary) | no | Compact summary of the latest known release candidate for the artifact. |
| <a id="artifactsdataentry-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] | no | Release-line summaries associated with the artifact. |
| <a id="artifactsdataentry-namedrefs"></a>`namedRefs` | list[[RefAggregateEntry](#refaggregateentry)] | no | Published development, line-head, or named-ref contexts associated with the artifact. |
| <a id="artifactsdataentry-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[NonEmptyString](#nonemptystring), [SupportStatusDefinition](#supportstatusdefinition)] | no | Reusable support-status definitions that release lines and releases for this artifact can refer to by key. |
| <a id="artifactsdataentry-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) | no | Canonical URL for the support policy document associated with this artifact. |

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
| <a id="candidateaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | Provider key for the upstream system that supplied this candidate record. |
| <a id="candidateaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | Provider-specific stable identifier for the upstream candidate record. |
| <a id="candidateaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | Human-browsable upstream URL for the candidate record. |
| <a id="candidateaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the candidate. |
| <a id="candidateaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | Owning artifact key for the candidate. |
| <a id="candidateaggregateentry-version"></a>`version` | [VersionString](#versionstring) | yes | Candidate version string represented by this aggregate entry. |
| <a id="candidateaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | Human-readable candidate label when it should differ from the raw version string. |
| <a id="candidateaggregateentry-candidatesequence"></a>`candidateSequence` | int | no | Numeric ordering hint for the candidate, usually the `rc` sequence number. |
| <a id="candidateaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key that the candidate belongs to, if known. |
| <a id="candidateaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Maturity label associated with the candidate. |
| <a id="candidateaggregateentry-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | Vote-status label for the candidate, if known. |
| <a id="candidateaggregateentry-createdat"></a>`createdAt` | [TimestampString](#timestampstring) | no | Timestamp when the candidate record was first created. |
| <a id="candidateaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | Timestamp when the candidate became publicly visible. |
| <a id="candidateaggregateentry-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] | no | Downloadable assets attached to the candidate. |

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
| <a id="compatibilityaggregateentry-subjectid"></a>`subjectId` | [NonEmptyString](#nonemptystring) | yes | Typed reference or aggregate identifier for the subject of the compatibility statement. |
| <a id="compatibilityaggregateentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | yes | Typed reference or aggregate identifier for the target of the compatibility statement. |
| <a id="compatibilityaggregateentry-relation"></a>`relation` | [NonEmptyString](#nonemptystring) | yes | Relationship label that names the compatibility statement. |
| <a id="compatibilityaggregateentry-scope"></a>`scope` | [NonEmptyString](#nonemptystring) | no | Optional scope label that narrows the compatibility statement. |
| <a id="compatibilityaggregateentry-confidence"></a>`confidence` | [NonEmptyString](#nonemptystring) | no | Optional confidence label that explains how strong the supporting evidence is. |
| <a id="compatibilityaggregateentry-notes"></a>`notes` | [NonEmptyString](#nonemptystring) | no | Additional human-readable explanation, caveats, or migration advice for the compatibility statement. |
| <a id="compatibilityaggregateentry-evidence"></a>`evidence` | list[[NonEmptyString](#nonemptystring)] | no | Named evidence pointers or short evidence labels that support the compatibility statement. |

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
| <a id="componentsdataentry-slug"></a>`slug` | [Slug](#slug) | yes | Stable component slug used by routes, aggregates, and typed references. |
| <a id="componentsdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable component name shown in navigation, listings, and generated metadata. |
| <a id="componentsdataentry-weight"></a>`weight` | int | no | Optional ordering hint copied from the authored catalog for consumer-rendered component lists. |
| <a id="componentsdataentry-group"></a>`group` | [Identifier](#identifier) | no | Optional group key copied from the authored catalog to support grouped rendering or filtering. |
| <a id="componentsdataentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | Origin key selected for this component's primary published route set. |
| <a id="componentsdataentry-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | Resolved publication roots and URLs for the component. |
| <a id="componentsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](#providerkey)] | no | Provider keys that contributed version metadata for this component's artifacts. |
| <a id="componentsdataentry-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] | no | Compact artifact summaries used by component listings and page chrome. |

#### Selected field examples

- `slug`: Example: `"spark"`
- `displayName`: Example: `"Apache Spark"`
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
| <a id="contentindexentry-id"></a>`id` | [NonEmptyString](#nonemptystring) | yes | Stable identifier for the indexed page entry. |
| <a id="contentindexentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the indexed page. |
| <a id="contentindexentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | Owning artifact key when the page belongs to a specific artifact. |
| <a id="contentindexentry-pagekind"></a>`pageKind` | [NonEmptyString](#nonemptystring) | yes | Short page-kind label used for filtering and presentation. |
| <a id="contentindexentry-section"></a>`section` | [NonEmptyString](#nonemptystring) | no | Higher-level section label used for navigation or filtering. |
| <a id="contentindexentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | Origin key that this indexed page belongs to. |
| <a id="contentindexentry-path"></a>`path` | [PublicPath](#publicpath) | yes | Published public path for the page. |
| <a id="contentindexentry-url"></a>`url` | [UrlString](#urlstring) | yes | Canonical absolute URL for the page. |
| <a id="contentindexentry-canonicalurl"></a>`canonicalUrl` | [UrlString](#urlstring) | no | Explicit canonical URL when it should differ from `url`. |
| <a id="contentindexentry-title"></a>`title` | [NonEmptyString](#nonemptystring) | no | Primary page title shown to readers. |
| <a id="contentindexentry-linktitle"></a>`linkTitle` | [NonEmptyString](#nonemptystring) | no | Shorter title variant used in navigation or link lists. |
| <a id="contentindexentry-description"></a>`description` | [NonEmptyString](#nonemptystring) | no | Longer page description intended for metadata or search snippets. |
| <a id="contentindexentry-summary"></a>`summary` | [NonEmptyString](#nonemptystring) | no | Short summary used for listings, cards, or lightweight search results. |
| <a id="contentindexentry-weight"></a>`weight` | int | no | Optional ordering hint used by renderers for listings or navigation. |
| <a id="contentindexentry-parentid"></a>`parentId` | [NonEmptyString](#nonemptystring) | no | Identifier of the parent indexed page when the page belongs to a hierarchy. |
| <a id="contentindexentry-ancestorids"></a>`ancestorIds` | list[[NonEmptyString](#nonemptystring)] | no | Ancestor page identifiers ordered from nearest to farthest. |
| <a id="contentindexentry-sourcepath"></a>`sourcePath` | [RepoRelativePath](#reporelativepath) | no | Repository-relative source file path for the page when it is known. |
| <a id="contentindexentry-versionkind"></a>`versionKind` | [RecordKind](#recordkind) | no | Version-context kind attached when the page belongs to a versioned route set. |
| <a id="contentindexentry-versionlabel"></a>`versionLabel` | [NonEmptyString](#nonemptystring) | no | Human-readable version label attached to the page, if present. |
| <a id="contentindexentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key attached to the page, if present. |
| <a id="contentindexentry-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label attached to the page's version context. |
| <a id="contentindexentry-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | Publication-state label attached to the page's version context. |
| <a id="contentindexentry-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | no | Locale key for the page when the page participates in localization. |
| <a id="contentindexentry-defaultlocale"></a>`defaultLocale` | bool | no | Whether the page represents the default locale within its translation group. |
| <a id="contentindexentry-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | no | Shared key that ties translated sibling pages together. |
| <a id="contentindexentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | Provider key for the upstream record that informed the page's version metadata. |
| <a id="contentindexentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | Provider-specific stable identifier for the upstream record that informed the page. |
| <a id="contentindexentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Maturity label such as preview, beta, or stable. |
| <a id="contentindexentry-candidatesequence"></a>`candidateSequence` | int | no | Release-candidate sequence number when the page belongs to a candidate context. |
| <a id="contentindexentry-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | Vote-status label when the page belongs to a candidate context. |

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
- `sourcePath`: Example: `"docs/runtime/getting-started.md"`
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
| <a id="latestcandidatesummary-version"></a>`version` | [VersionString](#versionstring) | no | Candidate version string when the provider exposes one. |
| <a id="latestcandidatesummary-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | Human-readable candidate label when it should differ from the raw version string. |
| <a id="latestcandidatesummary-candidatesequence"></a>`candidateSequence` | int | no | Numeric ordering hint for the candidate, usually the `rc` sequence number. |
| <a id="latestcandidatesummary-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | Vote-status label for the latest candidate when it is known. |

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
| <a id="latestreleasesummary-version"></a>`version` | [VersionString](#versionstring) | yes | Exact version string of the latest known release. |
| <a id="latestreleasesummary-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | Human-readable label for the latest release when it should differ from the raw version string. |
| <a id="latestreleasesummary-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | Tag associated with the latest release, if known. |
| <a id="latestreleasesummary-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | Publication-state label for the latest release, such as published or withdrawn. |
| <a id="latestreleasesummary-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | Timestamp when the latest release became publicly available. |

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
| <a id="mountaggregateentry-mountid"></a>`mountId` | [NonEmptyString](#nonemptystring) | yes | Stable aggregate identifier for the mount entry. |
| <a id="mountaggregateentry-ownerid"></a>`ownerId` | [NonEmptyString](#nonemptystring) | yes | Aggregate identifier for the component or artifact that owns the mount. |
| <a id="mountaggregateentry-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | Short mount kind label that tells consumers what sort of subtree this is. |
| <a id="mountaggregateentry-trustclass"></a>`trustClass` | [TrustClass](#trustclass) | yes | Trust level assigned to the mounted content. |
| <a id="mountaggregateentry-publicpath"></a>`publicPath` | [PublicPath](#publicpath) | yes | Public path where the mounted subtree is published. |
| <a id="mountaggregateentry-sourceref"></a>`sourceRef` | [MountSourceRef](#mountsourceref) | yes | Typed source reference for the generated or imported subtree being mounted. |
| <a id="mountaggregateentry-versioncontext"></a>`versionContext` | [NonEmptyString](#nonemptystring) | no | Optional version-context label that scopes the mount to one publication context. |
| <a id="mountaggregateentry-indexbehavior"></a>`indexBehavior` | [IndexBehavior](#indexbehavior) | no | How the mounted subtree should participate in generated indexes or listings. |
| <a id="mountaggregateentry-metadata"></a>`metadata` | [ExtensionsObject](#extensionsobject) | no | Small JSON-like extension object for extra mount metadata consumed by downstream tooling. |

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
| <a id="providersdataentry-key"></a>`key` | [ProviderKey](#providerkey) | yes | Stable provider identifier used by aggregate entries that originate from this provider. |
| <a id="providersdataentry-type"></a>`type` | [NonEmptyString](#nonemptystring) | yes | Provider implementation type, such as `github` or another fetcher backend label. |
| <a id="providersdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | Human-readable provider label shown in generated metadata or diagnostics. |
| <a id="providersdataentry-baseurl"></a>`baseUrl` | [ProviderBaseUrl](#providerbaseurl) | no | Base URL of the provider service when records can link back to a human-browsable upstream origin. |
| <a id="providersdataentry-fetchedat"></a>`fetchedAt` | [TimestampString](#timestampstring) | yes | Timestamp when this provider descriptor was fetched or refreshed. |

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
| <a id="redirectaggregateentry-fromurl"></a>`fromUrl` | [UrlString](#urlstring) | yes | Absolute source URL that should redirect. |
| <a id="redirectaggregateentry-tourl"></a>`toUrl` | [UrlString](#urlstring) | yes | Absolute destination URL that the redirect should send readers to. |
| <a id="redirectaggregateentry-status"></a>`status` | int | yes | HTTP redirect status code emitted for this redirect. |
| <a id="redirectaggregateentry-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | Short explanation of why the redirect exists. |
| <a id="redirectaggregateentry-sourcekind"></a>`sourceKind` | [NonEmptyString](#nonemptystring) | no | Short label describing where the redirect originated, such as an alias or withdrawn release rule. |

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
| <a id="refaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | Provider key for the upstream system that supplied this ref record. |
| <a id="refaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | Provider-specific stable identifier for the upstream ref record. |
| <a id="refaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | Human-browsable upstream URL for the ref record. |
| <a id="refaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the ref context. |
| <a id="refaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | Owning artifact key for the ref context. |
| <a id="refaggregateentry-kind"></a>`kind` | [RecordKind](#recordkind) | yes | Ref context kind, limited to development, named-ref, and line-head entries. |
| <a id="refaggregateentry-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) | no | Catalog-authored named-ref key when this entry represents a named ref. |
| <a id="refaggregateentry-ref"></a>`ref` | [RefString](#refstring) | yes | Exact source-control ref for the published ref context. |
| <a id="refaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | Human-readable label for the ref context. |
| <a id="refaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key when the ref context represents a line head. |
| <a id="refaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Maturity label associated with the ref context. |

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
| <a id="releaseaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | Provider key for the upstream system that supplied this release record. |
| <a id="releaseaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | Provider-specific stable identifier for the upstream release record. |
| <a id="releaseaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | Human-browsable upstream URL for the release record. |
| <a id="releaseaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the release. |
| <a id="releaseaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | Owning artifact key for the release. |
| <a id="releaseaggregateentry-version"></a>`version` | [VersionString](#versionstring) | yes | Exact released version represented by this aggregate entry. |
| <a id="releaseaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | Human-readable version label when it should differ from the raw version string. |
| <a id="releaseaggregateentry-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | Exact tag associated with the release, if known. |
| <a id="releaseaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | Release-line key that groups this release with related versions. |
| <a id="releaseaggregateentry-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](#nonemptystring)] | no | Ancestor release-line keys ordered from nearest to farthest. |
| <a id="releaseaggregateentry-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | Support-status key or label associated with the release. |
| <a id="releaseaggregateentry-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes associated with the release. |
| <a id="releaseaggregateentry-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | Publication-state label for the release, such as published, withdrawn, or tombstoned. |
| <a id="releaseaggregateentry-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](#withdrawalbehavior) | no | Behavior that readers should experience when the release has been withdrawn. |
| <a id="releaseaggregateentry-redirecttarget"></a>`redirectTarget` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | no | Replacement route or external URL used when a withdrawn release redirects readers elsewhere. |
| <a id="releaseaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | Maturity label such as stable, preview, or beta. |
| <a id="releaseaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | Timestamp when the release became publicly available. |
| <a id="releaseaggregateentry-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] | no | Downloadable assets attached to the release. |
| <a id="releaseaggregateentry-urls"></a>`urls` | dict[[NonEmptyString](#nonemptystring), [UrlString](#urlstring)] | no | Additional named URLs related to the release, such as notes, downloads, or verification material. |

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
| <a id="routeaggregateentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | Origin key that this public route belongs to. |
| <a id="routeaggregateentry-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | Base URL for the route's origin. |
| <a id="routeaggregateentry-path"></a>`path` | [PublicPath](#publicpath) | yes | Public path for the route. |
| <a id="routeaggregateentry-url"></a>`url` | [UrlString](#urlstring) | yes | Absolute URL for the route after joining `baseUrl` and `path`. |
| <a id="routeaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the route. |
| <a id="routeaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | Owning artifact key when the route belongs to a specific artifact. |
| <a id="routeaggregateentry-section"></a>`section` | [NonEmptyString](#nonemptystring) | no | Higher-level section label for the route, if present. |
| <a id="routeaggregateentry-canonical"></a>`canonical` | bool | no | Whether this route should be treated as the canonical route among equivalent alternatives. |
| <a id="routeaggregateentry-routekind"></a>`routeKind` | [NonEmptyString](#nonemptystring) | no | Short route-kind label such as component root, docs root, alias, or release page. |
| <a id="routeaggregateentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | no | Stable target identifier used to correlate equivalent routes or aliases. |
| <a id="routeaggregateentry-label"></a>`label` | [NonEmptyString](#nonemptystring) | no | Human-readable label for the route, if present. |
| <a id="routeaggregateentry-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | no | Locale key when the route belongs to a localized page family. |

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
| <a id="translationsetaggregateentry-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | yes | Shared key that ties all translated sibling pages in this set together. |
| <a id="translationsetaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | Owning component slug for the translation set. |
| <a id="translationsetaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | Owning artifact key when the translation set belongs to a specific artifact. |
| <a id="translationsetaggregateentry-entries"></a>`entries` | list[[TranslationLinkSummary](#translationlinksummary)] | yes | Translated sibling pages that belong to the same translation set. |

#### Selected field examples

- `translationKey`: Example: `"spark-overview"`
- `componentSlug`: Example: `"spark"`
- `artifactKey`: Example: `"runtime"`

## Incremental bookkeeping types

Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`.

<a id="aggregatedependencyentryv1"></a>
### AggregateDependencyEntryV1

One coordinator-owned aggregate and the units that may change its payload.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="aggregatedependencyentryv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](#stagerelativepath) | yes | Coordinator-owned aggregate file inside the visible stage. |
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
| <a id="outputownershipclaimv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](#stagerelativepath) | yes | Owned path inside the visible stage. |

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

