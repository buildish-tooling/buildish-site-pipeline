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

- contract-file tables identify the stable on-disk file for each root contract when one exists
- field names are shown in their wire-format aliases
- type, enum, and scalar names link to their definitions below
- schema files are listed by checked-in filename for the matching root contract

## File contract index

### Authored input contracts

Consumer-owned and component-owned source-tree contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/component.yaml` | [ComponentMetadataDocumentV1](#componentmetadatadocumentv1) | `site-pipeline-component-v1.schema.json` | Component-owned metadata input. |
| `site/catalog.yaml` | [SiteCatalogDocumentV1](#sitecatalogdocumentv1) | `site-pipeline-catalog-v1.schema.json` | Consumer-authored site catalog input. |

### Provider input contracts

Provider-derived snapshot contracts that the pipeline reads.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/provider-snapshot.json` | [ProviderSnapshotDocumentV1](#providersnapshotdocumentv1) | `site-pipeline-provider-snapshot-v1.schema.json` | Provider-derived release snapshot input. |

### Pipeline-emitted file contracts

Stable files that the pipeline writes into staged or published output trees.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `data/_pipeline/aggregate-dependencies.json` | [AggregateDependencyMapV1](#aggregatedependencymapv1) | `site-pipeline-aggregate-dependencies-v1.schema.json` | Pipeline-emitted aggregate dependency map. |
| `data/_pipeline/output-ownership.json` | [OutputOwnershipMapV1](#outputownershipmapv1) | `site-pipeline-output-ownership-v1.schema.json` | Pipeline-emitted output ownership map. |
| `data/_pipeline/unit-contributions.json` | [PersistedUnitContributionsV1](#persistedunitcontributionsv1) | `site-pipeline-unit-contributions-v1.schema.json` | Pipeline-emitted unit contribution map. |
| `data/artifacts.json` | [ArtifactsDataEntry](#artifactsdataentry) | `site-pipeline-artifacts-data-v1.schema.json` | Pipeline-emitted artifact aggregate file. |
| `data/candidates.json` | [CandidateAggregateEntry](#candidateaggregateentry) | `site-pipeline-candidates-data-v1.schema.json` | Pipeline-emitted candidate aggregate file. |
| `data/compatibility.json` | [CompatibilityAggregateEntry](#compatibilityaggregateentry) | `site-pipeline-compatibility-data-v1.schema.json` | Pipeline-emitted compatibility aggregate file. |
| `data/components.json` | [ComponentsDataEntry](#componentsdataentry) | `site-pipeline-components-data-v1.schema.json` | Pipeline-emitted component aggregate file. |
| `data/content-index.json` | [ContentIndexEntry](#contentindexentry) | `site-pipeline-content-index-data-v1.schema.json` | Pipeline-emitted content index file. |
| `data/diagnostics.json` | [PipelineDiagnosticEntry](#pipelinediagnosticentry) | `site-pipeline-diagnostics-data-v1.schema.json` | Pipeline-emitted diagnostics file. |
| `data/mounts.json` | [MountAggregateEntry](#mountaggregateentry) | `site-pipeline-mounts-data-v1.schema.json` | Pipeline-emitted mount aggregate file. |
| `data/providers.json` | [ProvidersDataEntry](#providersdataentry) | `site-pipeline-providers-data-v1.schema.json` | Pipeline-emitted provider summary aggregate file. |
| `data/redirects.json` | [RedirectAggregateEntry](#redirectaggregateentry) | `site-pipeline-redirects-data-v1.schema.json` | Pipeline-emitted redirect aggregate file. |
| `data/refs.json` | [RefAggregateEntry](#refaggregateentry) | `site-pipeline-refs-data-v1.schema.json` | Pipeline-emitted named-ref aggregate file. |
| `data/releases.json` | [ReleaseAggregateEntry](#releaseaggregateentry) | `site-pipeline-releases-data-v1.schema.json` | Pipeline-emitted release aggregate file. |
| `data/routes.json` | [RouteAggregateEntry](#routeaggregateentry) | `site-pipeline-routes-data-v1.schema.json` | Pipeline-emitted route aggregate file. |
| `data/translations.json` | [TranslationSetAggregateEntry](#translationsetaggregateentry) | `site-pipeline-translations-data-v1.schema.json` | Pipeline-emitted translation aggregate file. |
| `manifest.json` | [StageManifestV1](#stagemanifestv1) | `site-pipeline-stage-manifest-v1.schema.json` | Pipeline-emitted stage manifest. |

### Pipeline-emitted non-file root contracts

Schema-root report and namespace types that do not correspond to one stable checked-in file path.

| Root type(s) | Schema file | Summary |
| --- | --- | --- |
| [CheckReportV1](#checkreportv1) | `site-pipeline-check-report-v1.schema.json` | Pipeline-emitted validation report. |
| [PipelineFrontMatterNamespace](#pipelinefrontmatternamespace) | `site-pipeline-front-matter-namespace-v1.schema.json` | Pipeline-emitted front matter namespace. |
| [ResolvedMaterializationReportV1](#resolvedmaterializationreportv1) | `site-pipeline-materialization-report-v1.schema.json` | Pipeline-emitted materialization report. |
| [StageRunReportV1](#stagerunreportv1) | `site-pipeline-stage-run-report-v1.schema.json` | Pipeline-emitted stage execution report. |

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
| <a id="routemode"></a>`RouteMode` | `none`, `prefixAll` | Locale routing strategy for one publication surface. |
| <a id="runstatus"></a>`RunStatus` | `clean`, `warnings`, `errors` | Overall diagnostic class for a run or cycle. |
| <a id="stagecommand"></a>`StageCommand` | `build`, `watch` | Stable stage-producing command modes. |
| <a id="trustclass"></a>`TrustClass` | `passive`, `active` | Trust posture of a mounted content subtree. |
| <a id="withdrawalbehavior"></a>`WithdrawalBehavior` | `notice`, `redirect`, `omit` | Author-directed behavior for a withdrawn release. |


## Type index

### Authored input types

Consumer-owned and component-owned authored contract models.

- [ArtifactConfig](#artifactconfig) — Independently versioned release unit within a component.
- [ArtifactLifecycleConfig](#artifactlifecycleconfig) — Artifact-authored lifecycle metadata.
- [ArtifactVersioningConfig](#artifactversioningconfig) — Artifact-specific version-discovery configuration.
- [CandidateSelectionPolicy](#candidateselectionpolicy) — Selection policy for release candidates.
- [CatalogDefaults](#catalogdefaults) — Shared defaults applied before per-component overrides.
- [CompatibilityAssertionConfig](#compatibilityassertionconfig) — Authored compatibility relationship between published identities.
- [ComponentCatalogEntry](#componentcatalogentry) — One component entry in the consumer catalog.
- [ComponentContentSelection](#componentcontentselection) — Selection of the source that owns shared component content.
- [ComponentIdentity](#componentidentity) — Stable identity for a component repository.
- [ComponentLifecycleHints](#componentlifecyclehints) — Optional high-level lifecycle defaults for a component.
- [ComponentMetadataDocumentV1](#componentmetadatadocumentv1) — Component-owned metadata that describes stable identity and repository content roots.
- [ContentRoots](#contentroots) — Repository-relative locations of authored component content.
- [ExactReleaseConfig](#exactreleaseconfig) — Authored exact-release metadata or publication override for one version.
- [GroupConfig](#groupconfig) — Reusable defaults for a set of components.
- [LineHeadSelectionPolicy](#lineheadselectionpolicy) — Selection policy for release-line head refs.
- [LocalizationConfig](#localizationconfig) — Locale and translation defaults.
- [MountConfig](#mountconfig) — Generated or imported subtree mounted into the publication surface.
- [NamedRefConfig](#namedrefconfig) — Authored named ref intentionally exposed as a publishable version context.
- [OriginConfig](#originconfig) — Named publication origin.
- [PublicationConfig](#publicationconfig) — Explicit publication configuration or inherited publication defaults.
- [PublicationSelectionPolicy](#publicationselectionpolicy) — Planning-time policy for which version contexts are staged and surfaced.
- [RedirectRuleConfig](#redirectruleconfig) — Authored redirect rule resolved into deployment-neutral redirect metadata.
- [ReleaseLineConfig](#releaselineconfig) — Artifact-authored release-line definition.
- [ReleaseSelectionPolicy](#releaseselectionpolicy) — Selection policy for exact released versions.
- [RouteAliasConfig](#routealiasconfig) — Additional route resolving to the same published target.
- [SiteCatalogDocumentV1](#sitecatalogdocumentv1) — Consumer-owned catalog input that selects participating components and shared publication policy.
- [SiteContentConfig](#sitecontentconfig) — Consumer-owned top-level site pages, assets, and vendor assets.
- [SourceConfig](#sourceconfig) — Repository or checkout definition.
- [SupportStatusDefinition](#supportstatusdefinition) — Definition of one support-status vocabulary entry.
- [SupportWindow](#supportwindow) — Structured support-window metadata for a line or exact release.

### Provider input types

Normalized provider snapshot contracts consumed by the pipeline.

- [ProviderAsset](#providerasset) — Optional file-level metadata attached to a provider record.
- [ProviderDescriptor](#providerdescriptor) — Descriptor for one loaded provider.
- [ProviderRecord](#providerrecord) — Normalized release, candidate, or ref record from a provider.
- [ProviderSnapshotDocumentV1](#providersnapshotdocumentv1) — Provider-derived normalized snapshot from ``site/provider-snapshot.json``.

### Planning and stage-contract types

Pipeline-emitted planning, diagnostics, and stage-manifest contracts.

- [CheckReportV1](#checkreportv1) — Machine-readable result of ``site-pipeline check``.
- [CheckSummary](#checksummary) — Outcome summary for one ``check`` run.
- [PipelineDiagnosticEntry](#pipelinediagnosticentry) — Structured pipeline diagnostic entry.
- [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) — Bounded replacement object for oversized diagnostic details.
- [ResolvedMaterializationEntry](#resolvedmaterializationentry) — One required local input discovered by planning.
- [ResolvedMaterializationReportV1](#resolvedmaterializationreportv1) — Machine-readable planning report for required local inputs.
- [StageDataFiles](#stagedatafiles) — Inventory of aggregate metadata files present in a stage tree.
- [StageManifestV1](#stagemanifestv1) — Authoritative entry-point document for a staged output tree.
- [StageRoots](#stageroots) — Top-level directory roots within a stage tree.
- [StageRunReportV1](#stagerunreportv1) — Machine-readable result of ``build`` or one completed watch cycle.
- [StageRunSummary](#stagerunsummary) — Outcome summary for one stage-producing run or watch cycle.

### Staged front matter types

Front matter and page-level metadata emitted into staged content.

- [ArtifactFrontMatterSummary](#artifactfrontmattersummary) — Compact artifact summary embedded in component front matter.
- [PipelineComponentFrontMatter](#pipelinecomponentfrontmatter) — Pipeline-owned component front matter.
- [PipelineFrontMatterNamespace](#pipelinefrontmatternamespace) — Reserved top-level pipeline namespace emitted into staged pages.
- [PipelinePageFrontMatter](#pipelinepagefrontmatter) — Pipeline-owned page-local front matter.
- [ProviderProvenance](#providerprovenance) — Compact provider provenance embedded in page front matter.
- [ReleaseLineContext](#releaselinecontext) — Page-local release-line context.
- [ReleaseLineSummary](#releaselinesummary) — Compact release-line summary embedded into front matter.
- [ResolvedOrigin](#resolvedorigin) — Resolved publication origin information.
- [ResolvedPathSet](#resolvedpathset) — Resolved public paths for one component.
- [ResolvedPublication](#resolvedpublication) — Resolved route and URL bundle for one component.
- [ResolvedUrlSet](#resolvedurlset) — Resolved fully qualified URLs for one component.
- [TranslationLinkSummary](#translationlinksummary) — Compact translation sibling reference.
- [VersionContext](#versioncontext) — Version or ref context attached to one staged page.

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

Independently versioned release unit within a component.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactconfig-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-source"></a>`source` | [SourceKey](#sourcekey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-versioning"></a>`versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-publicationselection"></a>`publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-lifecycle"></a>`lifecycle` | [ArtifactLifecycleConfig](#artifactlifecycleconfig) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-compatibility"></a>`compatibility` | list[[CompatibilityAssertionConfig](#compatibilityassertionconfig)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactconfig-mounts"></a>`mounts` | list[[MountConfig](#mountconfig)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="artifactlifecycleconfig"></a>
### ArtifactLifecycleConfig

Artifact-authored lifecycle metadata.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactlifecycleconfig-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactlifecycleconfig-releaselines"></a>`releaseLines` | list[[ReleaseLineConfig](#releaselineconfig)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactlifecycleconfig-releases"></a>`releases` | list[[ExactReleaseConfig](#exactreleaseconfig)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactlifecycleconfig-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](#identifier), [SupportStatusDefinition](#supportstatusdefinition)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactlifecycleconfig-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactlifecycleconfig-defaultsupportwindow"></a>`defaultSupportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="artifactversioningconfig"></a>
### ArtifactVersioningConfig

Artifact-specific version-discovery configuration.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactversioningconfig-developmentref"></a>`developmentRef` | [RefString](#refstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactversioningconfig-maintenancerefpattern"></a>`maintenanceRefPattern` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactversioningconfig-tagpattern"></a>`tagPattern` | [RegexString](#regexstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactversioningconfig-namedrefs"></a>`namedRefs` | list[[NamedRefConfig](#namedrefconfig)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="candidateselectionpolicy"></a>
### CandidateSelectionPolicy

Selection policy for release candidates.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="candidateselectionpolicy-mode"></a>`mode` | [CandidateSelectionMode](#candidateselectionmode) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateselectionpolicy-versions"></a>`versions` | list[[VersionString](#versionstring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateselectionpolicy-externalids"></a>`externalIds` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

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

Authored compatibility relationship between published identities.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="compatibilityassertionconfig-subjectref"></a>`subjectRef` | [ReferenceString](#referencestring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityassertionconfig-targetref"></a>`targetRef` | [ReferenceString](#referencestring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityassertionconfig-relation"></a>`relation` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityassertionconfig-scope"></a>`scope` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityassertionconfig-confidence"></a>`confidence` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityassertionconfig-notes"></a>`notes` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="componentcatalogentry"></a>
### ComponentCatalogEntry

One component entry in the consumer catalog.

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

Selection of the source that owns shared component content.

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

Optional high-level lifecycle defaults for a component.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentlifecyclehints-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | Latest stable version for the component when one overall release line is enough. |
| <a id="componentlifecyclehints-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](#identifier), [SupportStatusDefinition](#supportstatusdefinition)] | no | Optional support-status vocabulary shared by artifacts in this repository. |

<a id="componentmetadatadocumentv1"></a>
### ComponentMetadataDocumentV1

Component-owned metadata that describes stable identity and repository content roots.

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

Authored exact-release metadata or publication override for one version.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="exactreleaseconfig-version"></a>`version` | [VersionString](#versionstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](#withdrawalbehavior) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-redirecttarget"></a>`redirectTarget` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="exactreleaseconfig-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="groupconfig"></a>
### GroupConfig

Reusable defaults for a set of components.

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

Selection policy for release-line head refs.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="lineheadselectionpolicy-mode"></a>`mode` | [LineHeadSelectionMode](#lineheadselectionmode) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="lineheadselectionpolicy-keys"></a>`keys` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

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

Generated or imported subtree mounted into the publication surface.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountconfig-source"></a>`source` | [MountSourceRef](#mountsourceref) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-mountpath"></a>`mountPath` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-trustclass"></a>`trustClass` | [TrustClass](#trustclass) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-versionscope"></a>`versionScope` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-indexbehavior"></a>`indexBehavior` | [IndexBehavior](#indexbehavior) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-ownership"></a>`ownership` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountconfig-metadata"></a>`metadata` | [ExtensionsObject](#extensionsobject) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="namedrefconfig"></a>
### NamedRefConfig

Authored named ref intentionally exposed as a publishable version context.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="namedrefconfig-key"></a>`key` | [Identifier](#identifier) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="namedrefconfig-ref"></a>`ref` | [RefString](#refstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="namedrefconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="namedrefconfig-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="namedrefconfig-description"></a>`description` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="originconfig"></a>
### OriginConfig

Named publication origin.

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

Explicit publication configuration or inherited publication defaults.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationconfig-origin"></a>`origin` | [OriginKey](#originkey) | no | Publication origin key to use for this component or artifact. |
| <a id="publicationconfig-pathsegment"></a>`pathSegment` | [NonEmptyString](#nonemptystring) | no | Path segment appended below an inherited path prefix or mount root. |
| <a id="publicationconfig-mountpath"></a>`mountPath` | [PublicPath](#publicpath) | no | Explicit public root path for the component publication surface. |
| <a id="publicationconfig-componentpath"></a>`componentPath` | [PublicPath](#publicpath) | no | Explicit public path for the component landing page or overview root. |
| <a id="publicationconfig-developmentpath"></a>`developmentPath` | [PublicPath](#publicpath) | no | Explicit public path for the moving latest/development docs surface. |
| <a id="publicationconfig-docspath"></a>`docsPath` | [PublicPath](#publicpath) | no | Explicit public docs landing path exposed to downstream consumers; defaults to the development/latest path unless an additional docs segment or override is configured. |
| <a id="publicationconfig-assetspath"></a>`assetsPath` | [PublicPath](#publicpath) | no | Explicit public path for static assets below the component root. |
| <a id="publicationconfig-canonicalpath"></a>`canonicalPath` | [PublicPath](#publicpath) | no | Optional canonical public path used when aliases or multiple origins are present. |
| <a id="publicationconfig-aliases"></a>`aliases` | list[[RouteAliasConfig](#routealiasconfig)] | no | Additional public aliases that should resolve to the same published target. |
| <a id="publicationconfig-redirects"></a>`redirects` | list[[RedirectRuleConfig](#redirectruleconfig)] | no | Redirect rules to emit for legacy or moved routes. |

<a id="publicationselectionpolicy"></a>
### PublicationSelectionPolicy

Planning-time policy for which version contexts are staged and surfaced.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationselectionpolicy-development"></a>`development` | bool | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="publicationselectionpolicy-lineheads"></a>`lineHeads` | [LineHeadSelectionPolicy](#lineheadselectionpolicy) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="publicationselectionpolicy-releases"></a>`releases` | [ReleaseSelectionPolicy](#releaseselectionpolicy) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="publicationselectionpolicy-namedrefs"></a>`namedRefs` | list[[Identifier](#identifier)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="publicationselectionpolicy-candidates"></a>`candidates` | [CandidateSelectionPolicy](#candidateselectionpolicy) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="redirectruleconfig"></a>
### RedirectRuleConfig

Authored redirect rule resolved into deployment-neutral redirect metadata.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="redirectruleconfig-frompath"></a>`fromPath` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectruleconfig-fromorigin"></a>`fromOrigin` | [OriginKey](#originkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectruleconfig-target"></a>`target` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectruleconfig-status"></a>`status` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectruleconfig-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="releaselineconfig"></a>
### ReleaseLineConfig

Artifact-authored release-line definition.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselineconfig-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-parent"></a>`parent` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-latest"></a>`latest` | [VersionString](#versionstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-aliases"></a>`aliases` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-maintenanceref"></a>`maintenanceRef` | [RefString](#refstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselineconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="releaseselectionpolicy"></a>
### ReleaseSelectionPolicy

Selection policy for exact released versions.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaseselectionpolicy-mode"></a>`mode` | [ReleaseSelectionMode](#releaseselectionmode) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseselectionpolicy-count"></a>`count` | [PositiveInteger](#positiveinteger) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseselectionpolicy-versions"></a>`versions` | list[[VersionString](#versionstring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="routealiasconfig"></a>
### RouteAliasConfig

Additional route resolving to the same published target.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="routealiasconfig-path"></a>`path` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routealiasconfig-origin"></a>`origin` | [OriginKey](#originkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routealiasconfig-label"></a>`label` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="sitecatalogdocumentv1"></a>
### SiteCatalogDocumentV1

Consumer-owned catalog input that selects participating components and shared publication policy.

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

#### Example: Catalog with one component, one artifact, and release selection policy.

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

Consumer-owned top-level site pages, assets, and vendor assets.

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

Repository or checkout definition.

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

Definition of one support-status vocabulary entry.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportstatusdefinition-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportstatusdefinition-order"></a>`order` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportstatusdefinition-description"></a>`description` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportstatusdefinition-defaultmaintenancephase"></a>`defaultMaintenancePhase` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="supportwindow"></a>
### SupportWindow

Structured support-window metadata for a line or exact release.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportwindow-releasedate"></a>`releaseDate` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportwindow-maintenancephase"></a>`maintenancePhase` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportwindow-endofactivesupportdate"></a>`endOfActiveSupportDate` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportwindow-endofsupportdate"></a>`endOfSupportDate` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportwindow-endoflifedate"></a>`endOfLifeDate` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportwindow-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="supportwindow-notes"></a>`notes` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

## Provider input types

Normalized provider snapshot contracts consumed by the pipeline.

<a id="providerasset"></a>
### ProviderAsset

Optional file-level metadata attached to a provider record.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerasset-name"></a>`name` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-url"></a>`url` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-mediatype"></a>`mediaType` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-size"></a>`size` | [NonNegativeInteger](#nonnegativeinteger) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-checksums"></a>`checksums` | dict[[Identifier](#identifier), [NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-signatureurl"></a>`signatureUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-sbomurl"></a>`sbomUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerasset-provenanceurl"></a>`provenanceUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="providerdescriptor"></a>
### ProviderDescriptor

Descriptor for one loaded provider.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerdescriptor-key"></a>`key` | [ProviderKey](#providerkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerdescriptor-type"></a>`type` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerdescriptor-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerdescriptor-baseurl"></a>`baseUrl` | [ProviderBaseUrl](#providerbaseurl) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerdescriptor-fetchedat"></a>`fetchedAt` | [TimestampString](#timestampstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="providerrecord"></a>
### ProviderRecord

Normalized release, candidate, or ref record from a provider.

- category: `provider`
- ownership: `provider-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerrecord-provider"></a>`provider` | [ProviderKey](#providerkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-kind"></a>`kind` | [RecordKind](#recordkind) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-sourcekey"></a>`sourceKey` | [SourceKey](#sourcekey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-version"></a>`version` | [VersionString](#versionstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-ref"></a>`ref` | [RefString](#refstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-commitsha"></a>`commitSha` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-candidatesequence"></a>`candidateSequence` | [NonNegativeInteger](#nonnegativeinteger) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-createdat"></a>`createdAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-updatedat"></a>`updatedAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-urls"></a>`urls` | dict[[NonEmptyString](#nonemptystring), [UrlString](#urlstring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerrecord-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="providersnapshotdocumentv1"></a>
### ProviderSnapshotDocumentV1

Provider-derived normalized snapshot from `site/provider-snapshot.json`.

- category: `provider`
- ownership: `provider-derived`
- file contract: `site/provider-snapshot.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providersnapshotdocumentv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providersnapshotdocumentv1-providers"></a>`providers` | list[[ProviderDescriptor](#providerdescriptor)] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providersnapshotdocumentv1-records"></a>`records` | list[[ProviderRecord](#providerrecord)] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

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
| <a id="checkreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checkreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checkreportv1-command"></a>`command` | Literal['check'] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checkreportv1-summary"></a>`summary` | [CheckSummary](#checksummary) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checkreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="checksummary"></a>
### CheckSummary

Outcome summary for one `check` run.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checksummary-status"></a>`status` | [RunStatus](#runstatus) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checksummary-passed"></a>`passed` | bool | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checksummary-failonseverity"></a>`failOnSeverity` | [CheckFailureThreshold](#checkfailurethreshold) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checksummary-errorcount"></a>`errorCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checksummary-warningcount"></a>`warningCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="checksummary-infocount"></a>`infoCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="pipelinediagnosticentry"></a>
### PipelineDiagnosticEntry

Structured pipeline diagnostic entry.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinediagnosticentry-severity"></a>`severity` | [DiagnosticSeverity](#diagnosticseverity) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinediagnosticentry-code"></a>`code` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinediagnosticentry-message"></a>`message` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinediagnosticentry-componentslug"></a>`componentSlug` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinediagnosticentry-artifactkey"></a>`artifactKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinediagnosticentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinediagnosticentry-details"></a>`details` | [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) \| [ExtensionsObject](#extensionsobject) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="reduceddiagnosticdetailssummary"></a>
### ReducedDiagnosticDetailsSummary

Bounded replacement object for oversized diagnostic details.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="reduceddiagnosticdetailssummary-omitted"></a>`omitted` | Literal[True] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="reduceddiagnosticdetailssummary-reason"></a>`reason` | Literal['sizeLimitExceeded'] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="reduceddiagnosticdetailssummary-actualbytes"></a>`actualBytes` | [PositiveInteger](#positiveinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="reduceddiagnosticdetailssummary-limitbytes"></a>`limitBytes` | [PositiveInteger](#positiveinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="reduceddiagnosticdetailssummary-summary"></a>`summary` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="reduceddiagnosticdetailssummary-fingerprint"></a>`fingerprint` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="resolvedmaterializationentry"></a>
### ResolvedMaterializationEntry

One required local input discovered by planning.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationentry-sourcekey"></a>`sourceKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-inputkind"></a>`inputKind` | [MaterializationInputKind](#materializationinputkind) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-componentslug"></a>`componentSlug` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-artifactkey"></a>`artifactKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-version"></a>`version` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-ref"></a>`ref` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-commitsha"></a>`commitSha` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-expectedlocalpath"></a>`expectedLocalPath` | [LocalPathString](#localpathstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-status"></a>`status` | [MaterializationStatus](#materializationstatus) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-provenance"></a>`provenance` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-watcheligible"></a>`watchEligible` | bool | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationentry-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="resolvedmaterializationreportv1"></a>
### ResolvedMaterializationReportV1

Machine-readable planning report for required local inputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationreportv1-target"></a>`target` | [PlanningTarget](#planningtarget) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationreportv1-entries"></a>`entries` | list[[ResolvedMaterializationEntry](#resolvedmaterializationentry)] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedmaterializationreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="stagedatafiles"></a>
### StageDataFiles

Inventory of aggregate metadata files present in a stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedatafiles-components"></a>`components` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-artifacts"></a>`artifacts` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-routes"></a>`routes` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-redirects"></a>`redirects` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-releases"></a>`releases` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-candidates"></a>`candidates` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-refs"></a>`refs` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-translations"></a>`translations` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-compatibility"></a>`compatibility` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-mounts"></a>`mounts` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-providers"></a>`providers` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-contentindex"></a>`contentIndex` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-diagnostics"></a>`diagnostics` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-unitcontributions"></a>`unitContributions` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-outputownership"></a>`outputOwnership` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedatafiles-aggregatedependencies"></a>`aggregateDependencies` | [StageRelativePath](#stagerelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="stagemanifestv1"></a>
### StageManifestV1

Authoritative entry-point document for a staged output tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `manifest.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagemanifestv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-stagelayoutversion"></a>`stageLayoutVersion` | [SchemaVersion](#schemaversion) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-command"></a>`command` | [StageCommand](#stagecommand) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-frontmatterformat"></a>`frontMatterFormat` | Literal['yaml'] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-aggregateformat"></a>`aggregateFormat` | Literal['json'] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-roots"></a>`roots` | [StageRoots](#stageroots) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagemanifestv1-datafiles"></a>`dataFiles` | [StageDataFiles](#stagedatafiles) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="stageroots"></a>
### StageRoots

Top-level directory roots within a stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stageroots-content"></a>`content` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stageroots-static"></a>`static` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stageroots-data"></a>`data` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="stagerunreportv1"></a>
### StageRunReportV1

Machine-readable result of `build` or one completed watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-command"></a>`command` | [StageCommand](#stagecommand) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-summary"></a>`summary` | [StageRunSummary](#stagerunsummary) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-stagerootpath"></a>`stageRootPath` | [LocalPathString](#localpathstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-manifestpath"></a>`manifestPath` | [LocalPathString](#localpathstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-cycle"></a>`cycle` | [NonNegativeInteger](#nonnegativeinteger) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="stagerunsummary"></a>
### StageRunSummary

Outcome summary for one stage-producing run or watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunsummary-status"></a>`status` | [RunStatus](#runstatus) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunsummary-succeeded"></a>`succeeded` | bool | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunsummary-wrotestage"></a>`wroteStage` | bool | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunsummary-stageusable"></a>`stageUsable` | bool | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunsummary-errorcount"></a>`errorCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunsummary-warningcount"></a>`warningCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagerunsummary-infocount"></a>`infoCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

## Staged front matter types

Front matter and page-level metadata emitted into staged content.

<a id="artifactfrontmattersummary"></a>
### ArtifactFrontMatterSummary

Compact artifact summary embedded in component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactfrontmattersummary-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactfrontmattersummary-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactfrontmattersummary-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactfrontmattersummary-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="pipelinecomponentfrontmatter"></a>
### PipelineComponentFrontMatter

Pipeline-owned component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinecomponentfrontmatter-slug"></a>`slug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinecomponentfrontmatter-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinecomponentfrontmatter-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinecomponentfrontmatter-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="pipelinefrontmatternamespace"></a>
### PipelineFrontMatterNamespace

Reserved top-level pipeline namespace emitted into staged pages.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinefrontmatternamespace-component"></a>`component` | [PipelineComponentFrontMatter](#pipelinecomponentfrontmatter) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinefrontmatternamespace-page"></a>`page` | [PipelinePageFrontMatter](#pipelinepagefrontmatter) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="pipelinepagefrontmatter"></a>
### PipelinePageFrontMatter

Pipeline-owned page-local front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinepagefrontmatter-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-section"></a>`section` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-path"></a>`path` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-url"></a>`url` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-canonicalurl"></a>`canonicalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-alternateurls"></a>`alternateUrls` | list[[UrlString](#urlstring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-defaultlocale"></a>`defaultLocale` | bool | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-translations"></a>`translations` | list[[TranslationLinkSummary](#translationlinksummary)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-componentpath"></a>`componentPath` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-componenturl"></a>`componentUrl` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-version"></a>`version` | [VersionContext](#versioncontext) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="pipelinepagefrontmatter-provider"></a>`provider` | [ProviderProvenance](#providerprovenance) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="providerprovenance"></a>
### ProviderProvenance

Compact provider provenance embedded in page front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerprovenance-key"></a>`key` | [ProviderKey](#providerkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerprovenance-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providerprovenance-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="releaselinecontext"></a>
### ReleaseLineContext

Page-local release-line context.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselinecontext-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinecontext-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinecontext-ancestors"></a>`ancestors` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinecontext-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="releaselinesummary"></a>
### ReleaseLineSummary

Compact release-line summary embedded into front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselinesummary-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinesummary-parent"></a>`parent` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinesummary-latest"></a>`latest` | [VersionString](#versionstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinesummary-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinesummary-headref"></a>`headRef` | [RefString](#refstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinesummary-aliases"></a>`aliases` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaselinesummary-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="resolvedorigin"></a>
### ResolvedOrigin

Resolved publication origin information.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedorigin-key"></a>`key` | [OriginKey](#originkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedorigin-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedorigin-hostname"></a>`hostname` | [HostnameString](#hostnamestring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="resolvedpathset"></a>
### ResolvedPathSet

Resolved public paths for one component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedpathset-component"></a>`component` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedpathset-development"></a>`development` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedpathset-docs"></a>`docs` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedpathset-assets"></a>`assets` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="resolvedpublication"></a>
### ResolvedPublication

Resolved route and URL bundle for one component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedpublication-origin"></a>`origin` | [ResolvedOrigin](#resolvedorigin) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedpublication-paths"></a>`paths` | [ResolvedPathSet](#resolvedpathset) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedpublication-urls"></a>`urls` | [ResolvedUrlSet](#resolvedurlset) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="resolvedurlset"></a>
### ResolvedUrlSet

Resolved fully qualified URLs for one component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedurlset-component"></a>`component` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedurlset-development"></a>`development` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedurlset-docs"></a>`docs` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="resolvedurlset-assets"></a>`assets` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="translationlinksummary"></a>
### TranslationLinkSummary

Compact translation sibling reference.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="translationlinksummary-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="translationlinksummary-path"></a>`path` | [PublicPath](#publicpath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="translationlinksummary-url"></a>`url` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="translationlinksummary-title"></a>`title` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="versioncontext"></a>
### VersionContext

Version or ref context attached to one staged page.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="versioncontext-kind"></a>`kind` | [RecordKind](#recordkind) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-label"></a>`label` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-path"></a>`path` | [PublicPath](#publicpath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-url"></a>`url` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-docspath"></a>`docsPath` | [PublicPath](#publicpath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-docsurl"></a>`docsUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-ref"></a>`ref` | [RefString](#refstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-candidatesequence"></a>`candidateSequence` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-releaseline"></a>`releaseLine` | [ReleaseLineContext](#releaselinecontext) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="versioncontext-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

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
| <a id="artifactsdataentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-sourcekey"></a>`sourceKey` | [SourceKey](#sourcekey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](#providerkey)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-versioning"></a>`versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-lateststable"></a>`latestStable` | [VersionString](#versionstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-latestrelease"></a>`latestRelease` | [LatestReleaseSummary](#latestreleasesummary) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-latestcandidate"></a>`latestCandidate` | [LatestCandidateSummary](#latestcandidatesummary) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-namedrefs"></a>`namedRefs` | list[[RefAggregateEntry](#refaggregateentry)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[NonEmptyString](#nonemptystring), [SupportStatusDefinition](#supportstatusdefinition)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="artifactsdataentry-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="candidateaggregateentry"></a>
### CandidateAggregateEntry

Entry in `data/candidates.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="candidateaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-version"></a>`version` | [VersionString](#versionstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-candidatesequence"></a>`candidateSequence` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-createdat"></a>`createdAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="candidateaggregateentry-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="compatibilityaggregateentry"></a>
### CompatibilityAggregateEntry

Entry in `data/compatibility.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="compatibilityaggregateentry-subjectid"></a>`subjectId` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityaggregateentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityaggregateentry-relation"></a>`relation` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityaggregateentry-scope"></a>`scope` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityaggregateentry-confidence"></a>`confidence` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityaggregateentry-notes"></a>`notes` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="compatibilityaggregateentry-evidence"></a>`evidence` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="componentsdataentry"></a>
### ComponentsDataEntry

Entry in `data/components.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentsdataentry-slug"></a>`slug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="componentsdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="componentsdataentry-weight"></a>`weight` | int | no | Optional ordering hint copied from the authored catalog for consumer-rendered component lists. |
| <a id="componentsdataentry-group"></a>`group` | [Identifier](#identifier) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="componentsdataentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="componentsdataentry-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="componentsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](#providerkey)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="componentsdataentry-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="contentindexentry"></a>
### ContentIndexEntry

Entry in `data/content-index.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="contentindexentry-id"></a>`id` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-pagekind"></a>`pageKind` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-section"></a>`section` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-path"></a>`path` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-url"></a>`url` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-canonicalurl"></a>`canonicalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-title"></a>`title` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-linktitle"></a>`linkTitle` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-description"></a>`description` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-summary"></a>`summary` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-weight"></a>`weight` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-parentid"></a>`parentId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-ancestorids"></a>`ancestorIds` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-sourcepath"></a>`sourcePath` | [RepoRelativePath](#reporelativepath) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-versionkind"></a>`versionKind` | [RecordKind](#recordkind) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-versionlabel"></a>`versionLabel` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-defaultlocale"></a>`defaultLocale` | bool | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-candidatesequence"></a>`candidateSequence` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="contentindexentry-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="latestcandidatesummary"></a>
### LatestCandidateSummary

Compact latest-candidate summary embedded in artifact aggregates.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="latestcandidatesummary-version"></a>`version` | [VersionString](#versionstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestcandidatesummary-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestcandidatesummary-candidatesequence"></a>`candidateSequence` | int | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestcandidatesummary-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="latestreleasesummary"></a>
### LatestReleaseSummary

Compact latest-release summary embedded in artifact aggregates.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="latestreleasesummary-version"></a>`version` | [VersionString](#versionstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestreleasesummary-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestreleasesummary-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestreleasesummary-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="latestreleasesummary-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="mountaggregateentry"></a>
### MountAggregateEntry

Entry in `data/mounts.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountaggregateentry-mountid"></a>`mountId` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-ownerid"></a>`ownerId` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-trustclass"></a>`trustClass` | [TrustClass](#trustclass) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-publicpath"></a>`publicPath` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-sourceref"></a>`sourceRef` | [MountSourceRef](#mountsourceref) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-versioncontext"></a>`versionContext` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-indexbehavior"></a>`indexBehavior` | [IndexBehavior](#indexbehavior) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="mountaggregateentry-metadata"></a>`metadata` | [ExtensionsObject](#extensionsobject) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="providersdataentry"></a>
### ProvidersDataEntry

Entry in `data/providers.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providersdataentry-key"></a>`key` | [ProviderKey](#providerkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providersdataentry-type"></a>`type` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providersdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providersdataentry-baseurl"></a>`baseUrl` | [ProviderBaseUrl](#providerbaseurl) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="providersdataentry-fetchedat"></a>`fetchedAt` | [TimestampString](#timestampstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="redirectaggregateentry"></a>
### RedirectAggregateEntry

Entry in `data/redirects.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="redirectaggregateentry-fromurl"></a>`fromUrl` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectaggregateentry-tourl"></a>`toUrl` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectaggregateentry-status"></a>`status` | int | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectaggregateentry-reason"></a>`reason` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="redirectaggregateentry-sourcekind"></a>`sourceKind` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="refaggregateentry"></a>
### RefAggregateEntry

Entry in `data/refs.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="refaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-kind"></a>`kind` | [RecordKind](#recordkind) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-ref"></a>`ref` | [RefString](#refstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="refaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="releaseaggregateentry"></a>
### ReleaseAggregateEntry

Entry in `data/releases.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaseaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-version"></a>`version` | [VersionString](#versionstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-tag"></a>`tag` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](#nonemptystring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](#withdrawalbehavior) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-redirecttarget"></a>`redirectTarget` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="releaseaggregateentry-urls"></a>`urls` | dict[[NonEmptyString](#nonemptystring), [UrlString](#urlstring)] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="routeaggregateentry"></a>
### RouteAggregateEntry

Entry in `data/routes.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="routeaggregateentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-path"></a>`path` | [PublicPath](#publicpath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-url"></a>`url` | [UrlString](#urlstring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-section"></a>`section` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-canonical"></a>`canonical` | bool | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-routekind"></a>`routeKind` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-label"></a>`label` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="routeaggregateentry-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="translationsetaggregateentry"></a>
### TranslationSetAggregateEntry

Entry in `data/translations.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="translationsetaggregateentry-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="translationsetaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="translationsetaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="translationsetaggregateentry-entries"></a>`entries` | list[[TranslationLinkSummary](#translationlinksummary)] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

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
| <a id="aggregatedependencyentryv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="aggregatedependencyentryv1-dependentunitids"></a>`dependentUnitIds` | tuple[str, ...] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="aggregatedependencymapv1"></a>
### AggregateDependencyMapV1

Shared-output dependency map for the current first-wave coordinator outputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/aggregate-dependencies.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="aggregatedependencymapv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="aggregatedependencymapv1-entries"></a>`entries` | tuple[[AggregateDependencyEntryV1](#aggregatedependencyentryv1), ...] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="outputownershipclaimv1"></a>
### OutputOwnershipClaimV1

One exact published file or directory root together with its logical owner.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="outputownershipclaimv1-ownerid"></a>`ownerId` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="outputownershipclaimv1-unitid"></a>`unitId` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="outputownershipclaimv1-pathkind"></a>`pathKind` | Literal['directory', 'file'] | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="outputownershipclaimv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](#stagerelativepath) | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="outputownershipmapv1"></a>
### OutputOwnershipMapV1

Published ownership inventory used to prune retained stages safely.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/output-ownership.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="outputownershipmapv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="outputownershipmapv1-claims"></a>`claims` | tuple[[OutputOwnershipClaimV1](#outputownershipclaimv1), ...] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="persistedunitcontributionsv1"></a>
### PersistedUnitContributionsV1

Stable per-unit page contribution manifests retained in the visible stage.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/unit-contributions.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="persistedunitcontributionsv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="persistedunitcontributionsv1-units"></a>`units` | tuple[[UnitContributionManifestWire](#unitcontributionmanifestwire), ...] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="stagedpagecontributionwire"></a>
### StagedPageContributionWire

Metadata emitted by one page-staging worker for later aggregation.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedpagecontributionwire-stagerelativepath"></a>`stageRelativePath` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-componentslug"></a>`componentSlug` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-artifactkey"></a>`artifactKey` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-section"></a>`section` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-pagekind"></a>`pageKind` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-publicpath"></a>`publicPath` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-publicurl"></a>`publicUrl` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-componentpath"></a>`componentPath` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-componenturl"></a>`componentUrl` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-originkey"></a>`originKey` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-versioncontext"></a>`versionContext` | dict[str, object] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-versionkind"></a>`versionKind` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-versionref"></a>`versionRef` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-version"></a>`version` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-locale"></a>`locale` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-defaultlocale"></a>`defaultLocale` | bool | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-translationkey"></a>`translationKey` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-title"></a>`title` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-linktitle"></a>`linkTitle` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-sourcepath"></a>`sourcePath` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="stagedpagecontributionwire-canonicalurl"></a>`canonicalUrl` | str | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

<a id="unitcontributionmanifestwire"></a>
### UnitContributionManifestWire

Worker-emitted contribution fragment consumed by the coordinator.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="unitcontributionmanifestwire-unitid"></a>`unitId` | str | yes | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |
| <a id="unitcontributionmanifestwire-pages"></a>`pages` | tuple[[StagedPageContributionWire](#stagedpagecontributionwire), ...] | no | **UX warning:** field description missing; this violates the project's UX requirements. (not documented) |

