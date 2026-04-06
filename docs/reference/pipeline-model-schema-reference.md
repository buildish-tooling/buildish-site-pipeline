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

Generated from the Site Pipeline Pydantic models and checked-in reference metadata. Do not edit by hand; regenerate with `make schemas`.

This page is generated from the public model layer and the checked-in schema export registry.
It is the typed reference companion to the narrative maintenance and how-to docs.

## Scope and conventions

- field names are shown in their wire-format aliases
- type, enum, and scalar names link to their definitions below
- schema files are listed by checked-in filename for the matching root contract

## File contract index

### Authored input contracts

Consumer-owned and component-owned source-tree contracts.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/component.yaml` | [ComponentMetadataDocumentV1](#componentmetadatadocumentv1) | `site-pipeline-component-v1.schema.json` | Component-owned metadata input. |
| `site/catalog.yaml` | [SiteCatalogDocumentV1](#sitecatalogdocumentv1) | `site-pipeline-catalog-v1.schema.json` | Consumer-authored site catalog input. |

### Provider input contracts

Provider-derived snapshot contracts consumed by the pipeline.

| Contract file | Root type(s) | Schema file | Summary |
| --- | --- | --- | --- |
| `site/provider-snapshot.json` | [ProviderSnapshotDocumentV1](#providersnapshotdocumentv1) | `site-pipeline-provider-snapshot-v1.schema.json` | Provider-derived release snapshot input. |

### Pipeline-emitted file contracts

Stable files emitted by the pipeline into staged or published output trees.

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

Schema-root report and namespace types without one stable checked-in file path hint.

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
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactconfig-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="artifactconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="artifactconfig-source"></a>`source` | [SourceKey](#sourcekey) | yes | — |
| <a id="artifactconfig-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | — |
| <a id="artifactconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | — |
| <a id="artifactconfig-versioning"></a>`versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | yes | — |
| <a id="artifactconfig-publicationselection"></a>`publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) \| None | no | — |
| <a id="artifactconfig-lifecycle"></a>`lifecycle` | [ArtifactLifecycleConfig](#artifactlifecycleconfig) \| None | no | — |
| <a id="artifactconfig-compatibility"></a>`compatibility` | list[[CompatibilityAssertionConfig](#compatibilityassertionconfig)] \| None | no | — |
| <a id="artifactconfig-mounts"></a>`mounts` | list[[MountConfig](#mountconfig)] \| None | no | — |

<a id="artifactlifecycleconfig"></a>
### ArtifactLifecycleConfig

Artifact-authored lifecycle metadata.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactlifecycleconfig-lateststable"></a>`latestStable` | [VersionString](#versionstring) \| None | no | — |
| <a id="artifactlifecycleconfig-releaselines"></a>`releaseLines` | list[[ReleaseLineConfig](#releaselineconfig)] \| None | no | — |
| <a id="artifactlifecycleconfig-releases"></a>`releases` | list[[ExactReleaseConfig](#exactreleaseconfig)] \| None | no | — |
| <a id="artifactlifecycleconfig-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](#identifier), [SupportStatusDefinition](#supportstatusdefinition)] \| None | no | — |
| <a id="artifactlifecycleconfig-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="artifactlifecycleconfig-defaultsupportwindow"></a>`defaultSupportWindow` | [SupportWindow](#supportwindow) \| None | no | — |

<a id="artifactversioningconfig"></a>
### ArtifactVersioningConfig

Artifact-specific version-discovery configuration.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactversioningconfig-developmentref"></a>`developmentRef` | [RefString](#refstring) | yes | — |
| <a id="artifactversioningconfig-maintenancerefpattern"></a>`maintenanceRefPattern` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="artifactversioningconfig-tagpattern"></a>`tagPattern` | [RegexString](#regexstring) | yes | — |
| <a id="artifactversioningconfig-namedrefs"></a>`namedRefs` | list[[NamedRefConfig](#namedrefconfig)] \| None | no | — |

<a id="candidateselectionpolicy"></a>
### CandidateSelectionPolicy

Selection policy for release candidates.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="candidateselectionpolicy-mode"></a>`mode` | [CandidateSelectionMode](#candidateselectionmode) | yes | — |
| <a id="candidateselectionpolicy-versions"></a>`versions` | list[[VersionString](#versionstring)] \| None | no | — |
| <a id="candidateselectionpolicy-externalids"></a>`externalIds` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |

<a id="catalogdefaults"></a>
### CatalogDefaults

Shared defaults applied before per-component overrides.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="catalogdefaults-metadatafile"></a>`metadataFile` | [RepoRelativePath](#reporelativepath) \| None | no | Default location of `site/component.yaml` within each source tree. |
| <a id="catalogdefaults-pagesroot"></a>`pagesRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Default repository-relative root for non-versioned component pages. |
| <a id="catalogdefaults-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Default repository-relative root for component docs content. |
| <a id="catalogdefaults-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Default repository-relative root for component static assets. |
| <a id="catalogdefaults-publication"></a>`publication` | PublicationDefaults \| None | no | Shared publication defaults inherited by components unless they override them. |
| <a id="catalogdefaults-localization"></a>`localization` | [LocalizationConfig](#localizationconfig) \| None | no | Shared localization defaults inherited by components unless they override them. |

<a id="compatibilityassertionconfig"></a>
### CompatibilityAssertionConfig

Authored compatibility relationship between published identities.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="compatibilityassertionconfig-subjectref"></a>`subjectRef` | [ReferenceString](#referencestring) | yes | — |
| <a id="compatibilityassertionconfig-targetref"></a>`targetRef` | [ReferenceString](#referencestring) | yes | — |
| <a id="compatibilityassertionconfig-relation"></a>`relation` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="compatibilityassertionconfig-scope"></a>`scope` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="compatibilityassertionconfig-confidence"></a>`confidence` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="compatibilityassertionconfig-notes"></a>`notes` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="componentcatalogentry"></a>
### ComponentCatalogEntry

One component entry in the consumer catalog.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentcatalogentry-slug"></a>`slug` | [Slug](#slug) | yes | Stable component identifier. |
| <a id="componentcatalogentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | Human-readable component name override or convenience value. |
| <a id="componentcatalogentry-localdir"></a>`localDir` | [RepoRelativePath](#reporelativepath) \| None | no | Simple shorthand for binding the component to one workspace-local checkout directory. |
| <a id="componentcatalogentry-weight"></a>`weight` | int \| None | no | Optional ordering hint for component listings, menus, and other consumer-rendered component collections. |
| <a id="componentcatalogentry-group"></a>`group` | [Identifier](#identifier) \| None | no | Optional group key for inherited defaults and renderer grouping. |
| <a id="componentcatalogentry-content"></a>`content` | [ComponentContentSelection](#componentcontentselection) \| None | no | Shared content-source selection for component pages, docs, and assets. |
| <a id="componentcatalogentry-publication"></a>`publication` | [PublicationConfig](#publicationconfig) \| None | no | Explicit publication configuration for this component. |
| <a id="componentcatalogentry-publicationselection"></a>`publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) \| None | no | Default version-context selection policy inherited by contained artifacts unless they override it. |
| <a id="componentcatalogentry-localization"></a>`localization` | [LocalizationConfig](#localizationconfig) \| None | no | Component-specific localization overrides. |
| <a id="componentcatalogentry-compatibility"></a>`compatibility` | list[[CompatibilityAssertionConfig](#compatibilityassertionconfig)] \| None | no | Component-level compatibility assertions emitted into staged metadata. |
| <a id="componentcatalogentry-mounts"></a>`mounts` | list[[MountConfig](#mountconfig)] \| None | no | Component-level generated or imported documentation mounts. |
| <a id="componentcatalogentry-artifacts"></a>`artifacts` | list[[ArtifactConfig](#artifactconfig)] \| None | no | Independently versioned artifacts belonging to this component. |

<a id="componentcontentselection"></a>
### ComponentContentSelection

Selection of the source that owns shared component content.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentcontentselection-source"></a>`source` | [SourceKey](#sourcekey) \| None | no | Named source that owns shared component pages, docs, and assets roots. |

<a id="componentidentity"></a>
### ComponentIdentity

Stable identity for a component repository.

- category: `authored`
- ownership: `component-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentidentity-slug"></a>`slug` | [Slug](#slug) | yes | Stable component identifier used by consumer catalogs and staged metadata. |
| <a id="componentidentity-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | Human-readable component name shown in rendered navigation and listings. |

<a id="componentlifecyclehints"></a>
### ComponentLifecycleHints

Optional high-level lifecycle defaults for a component.

- category: `authored`
- ownership: `component-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentlifecyclehints-lateststable"></a>`latestStable` | [VersionString](#versionstring) \| None | no | Latest stable version for the component when one overall release line is enough. |
| <a id="componentlifecyclehints-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](#identifier), [SupportStatusDefinition](#supportstatusdefinition)] \| None | no | Optional support-status vocabulary shared by artifacts in this repository. |

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
| <a id="componentmetadatadocumentv1-content"></a>`content` | [ContentRoots](#contentroots) \| None | no | Repository-relative authored content roots owned by this component. |
| <a id="componentmetadatadocumentv1-lifecycle"></a>`lifecycle` | [ComponentLifecycleHints](#componentlifecyclehints) \| None | no | Optional high-level lifecycle hints shared across the component repository. |

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
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="contentroots-pagesroot"></a>`pagesRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Repository-relative root for non-versioned component-owned pages. |
| <a id="contentroots-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Repository-relative root for versioned or development docs content. |
| <a id="contentroots-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Repository-relative root for component-owned static assets. |

<a id="exactreleaseconfig"></a>
### ExactReleaseConfig

Authored exact-release metadata or publication override for one version.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="exactreleaseconfig-version"></a>`version` | [VersionString](#versionstring) | yes | — |
| <a id="exactreleaseconfig-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="exactreleaseconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="exactreleaseconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) \| None | no | — |
| <a id="exactreleaseconfig-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) \| None | no | — |
| <a id="exactreleaseconfig-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](#withdrawalbehavior) \| None | no | — |
| <a id="exactreleaseconfig-redirecttarget"></a>`redirectTarget` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) \| None | no | — |
| <a id="exactreleaseconfig-reason"></a>`reason` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="groupconfig"></a>
### GroupConfig

Reusable defaults for a set of components.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="groupconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | Human-readable group name for renderers or generated navigation. |
| <a id="groupconfig-pathprefix"></a>`pathPrefix` | [PublicPath](#publicpath) \| None | no | Shared public path prefix applied to grouped component publication roots. |
| <a id="groupconfig-navigationsection"></a>`navigationSection` | [NonEmptyString](#nonemptystring) \| None | no | Optional renderer-facing grouping label for navigation or listings. |
| <a id="groupconfig-weight"></a>`weight` | int \| None | no | Optional ordering hint shared by components in this group. |
| <a id="groupconfig-publication"></a>`publication` | [PublicationConfig](#publicationconfig) \| None | no | Publication defaults inherited by grouped components unless they override them. |

<a id="lineheadselectionpolicy"></a>
### LineHeadSelectionPolicy

Selection policy for release-line head refs.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="lineheadselectionpolicy-mode"></a>`mode` | [LineHeadSelectionMode](#lineheadselectionmode) | yes | — |
| <a id="lineheadselectionpolicy-keys"></a>`keys` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |

<a id="localizationconfig"></a>
### LocalizationConfig

Locale and translation defaults.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="localizationconfig-defaultlocale"></a>`defaultLocale` | [NonEmptyString](#nonemptystring) \| None | no | Default locale used when a page does not declare a more specific locale. |
| <a id="localizationconfig-supportedlocales"></a>`supportedLocales` | list[[NonEmptyString](#nonemptystring)] \| None | no | Supported locale keys for this site or component. |
| <a id="localizationconfig-routemode"></a>`routeMode` | [RouteMode](#routemode) \| None | no | How localized pages should be routed within the published URL space. |
| <a id="localizationconfig-fallbacklocale"></a>`fallbackLocale` | [NonEmptyString](#nonemptystring) \| None | no | Fallback locale used when a requested translation is unavailable. |

<a id="mountconfig"></a>
### MountConfig

Generated or imported subtree mounted into the publication surface.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountconfig-source"></a>`source` | [MountSourceRef](#mountsourceref) | yes | — |
| <a id="mountconfig-mountpath"></a>`mountPath` | [PublicPath](#publicpath) | yes | — |
| <a id="mountconfig-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="mountconfig-trustclass"></a>`trustClass` | [TrustClass](#trustclass) | yes | — |
| <a id="mountconfig-versionscope"></a>`versionScope` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="mountconfig-indexbehavior"></a>`indexBehavior` | [IndexBehavior](#indexbehavior) \| None | no | — |
| <a id="mountconfig-ownership"></a>`ownership` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="mountconfig-metadata"></a>`metadata` | [ExtensionsObject](#extensionsobject) \| None | no | — |

<a id="namedrefconfig"></a>
### NamedRefConfig

Authored named ref intentionally exposed as a publishable version context.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="namedrefconfig-key"></a>`key` | [Identifier](#identifier) | yes | — |
| <a id="namedrefconfig-ref"></a>`ref` | [RefString](#refstring) | yes | — |
| <a id="namedrefconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="namedrefconfig-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="namedrefconfig-description"></a>`description` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="originconfig"></a>
### OriginConfig

Named publication origin.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="originconfig-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | Base public URL for this publication origin. |
| <a id="originconfig-canonical"></a>`canonical` | bool \| None | no | Whether this origin should be treated as canonical when multiple origins publish the same target. |
| <a id="originconfig-labels"></a>`labels` | list[[NonEmptyString](#nonemptystring)] \| None | no | Optional human-readable labels for renderer or deployment tooling. |

<a id="publicationconfig"></a>
### PublicationConfig

Explicit publication configuration or inherited publication defaults.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationconfig-origin"></a>`origin` | [OriginKey](#originkey) \| None | no | Publication origin key to use for this component or artifact. |
| <a id="publicationconfig-pathsegment"></a>`pathSegment` | [NonEmptyString](#nonemptystring) \| None | no | Path segment appended below an inherited path prefix or mount root. |
| <a id="publicationconfig-mountpath"></a>`mountPath` | [PublicPath](#publicpath) \| None | no | Explicit public root path for the component publication surface. |
| <a id="publicationconfig-componentpath"></a>`componentPath` | [PublicPath](#publicpath) \| None | no | Explicit public path for the component landing page or overview root. |
| <a id="publicationconfig-developmentpath"></a>`developmentPath` | [PublicPath](#publicpath) \| None | no | Explicit public path for the moving latest/development docs surface. |
| <a id="publicationconfig-docspath"></a>`docsPath` | [PublicPath](#publicpath) \| None | no | Explicit public docs landing path exposed to downstream consumers; defaults to the development/latest path unless an additional docs segment or override is configured. |
| <a id="publicationconfig-assetspath"></a>`assetsPath` | [PublicPath](#publicpath) \| None | no | Explicit public path for static assets below the component root. |
| <a id="publicationconfig-canonicalpath"></a>`canonicalPath` | [PublicPath](#publicpath) \| None | no | Optional canonical public path used when aliases or multiple origins are present. |
| <a id="publicationconfig-aliases"></a>`aliases` | list[[RouteAliasConfig](#routealiasconfig)] \| None | no | Additional public aliases that should resolve to the same published target. |
| <a id="publicationconfig-redirects"></a>`redirects` | list[[RedirectRuleConfig](#redirectruleconfig)] \| None | no | Redirect rules to emit for legacy or moved routes. |

<a id="publicationselectionpolicy"></a>
### PublicationSelectionPolicy

Planning-time policy for which version contexts are staged and surfaced.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationselectionpolicy-development"></a>`development` | bool \| None | no | — |
| <a id="publicationselectionpolicy-lineheads"></a>`lineHeads` | [LineHeadSelectionPolicy](#lineheadselectionpolicy) \| None | no | — |
| <a id="publicationselectionpolicy-releases"></a>`releases` | [ReleaseSelectionPolicy](#releaseselectionpolicy) \| None | no | — |
| <a id="publicationselectionpolicy-namedrefs"></a>`namedRefs` | list[[Identifier](#identifier)] \| None | no | — |
| <a id="publicationselectionpolicy-candidates"></a>`candidates` | [CandidateSelectionPolicy](#candidateselectionpolicy) \| None | no | — |

<a id="redirectruleconfig"></a>
### RedirectRuleConfig

Authored redirect rule resolved into deployment-neutral redirect metadata.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="redirectruleconfig-frompath"></a>`fromPath` | [PublicPath](#publicpath) | yes | — |
| <a id="redirectruleconfig-fromorigin"></a>`fromOrigin` | [OriginKey](#originkey) \| None | no | — |
| <a id="redirectruleconfig-target"></a>`target` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) | yes | — |
| <a id="redirectruleconfig-status"></a>`status` | int \| None | no | — |
| <a id="redirectruleconfig-reason"></a>`reason` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="releaselineconfig"></a>
### ReleaseLineConfig

Artifact-authored release-line definition.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselineconfig-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="releaselineconfig-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaselineconfig-parent"></a>`parent` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaselineconfig-latest"></a>`latest` | [VersionString](#versionstring) | yes | — |
| <a id="releaselineconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaselineconfig-aliases"></a>`aliases` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="releaselineconfig-maintenanceref"></a>`maintenanceRef` | [RefString](#refstring) \| None | no | — |
| <a id="releaselineconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) \| None | no | — |

<a id="releaseselectionpolicy"></a>
### ReleaseSelectionPolicy

Selection policy for exact released versions.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaseselectionpolicy-mode"></a>`mode` | [ReleaseSelectionMode](#releaseselectionmode) | yes | — |
| <a id="releaseselectionpolicy-count"></a>`count` | [PositiveInteger](#positiveinteger) \| None | no | — |
| <a id="releaseselectionpolicy-versions"></a>`versions` | list[[VersionString](#versionstring)] \| None | no | — |

<a id="routealiasconfig"></a>
### RouteAliasConfig

Additional route resolving to the same published target.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="routealiasconfig-path"></a>`path` | [PublicPath](#publicpath) | yes | — |
| <a id="routealiasconfig-origin"></a>`origin` | [OriginKey](#originkey) \| None | no | — |
| <a id="routealiasconfig-label"></a>`label` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="sitecatalogdocumentv1"></a>
### SiteCatalogDocumentV1

Consumer-owned catalog input that selects participating components and shared publication policy.

- category: `authored`
- ownership: `consumer-owned`
- file contract: `site/catalog.yaml`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sitecatalogdocumentv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | Schema version for the catalog format. |
| <a id="sitecatalogdocumentv1-defaults"></a>`defaults` | [CatalogDefaults](#catalogdefaults) \| None | no | Shared default settings applied before per-component overrides. |
| <a id="sitecatalogdocumentv1-site"></a>`site` | [SiteContentConfig](#sitecontentconfig) \| None | no | Consumer-owned top-level site pages, assets, and vendor-asset declarations. |
| <a id="sitecatalogdocumentv1-origins"></a>`origins` | dict[[OriginKey](#originkey), [OriginConfig](#originconfig)] \| None | no | Named publication origins that components can target. |
| <a id="sitecatalogdocumentv1-sources"></a>`sources` | dict[[SourceKey](#sourcekey), [SourceConfig](#sourceconfig)] \| None | no | Named repository or checkout bindings used by components and artifacts. |
| <a id="sitecatalogdocumentv1-groups"></a>`groups` | dict[[Identifier](#identifier), [GroupConfig](#groupconfig)] \| None | no | Optional grouping defaults shared by multiple components. |
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
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sitecontentconfig-pagesroot"></a>`pagesRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Repository-relative root for consumer-owned top-level site pages. |
| <a id="sitecontentconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | Repository-relative root for consumer-owned top-level static assets. |
| <a id="sitecontentconfig-vendorassets"></a>`vendorAssets` | list[TopLevelAssetConfig] \| None | no | Additional imported asset trees mounted into the top-level site assets area. |

<a id="sourceconfig"></a>
### SourceConfig

Repository or checkout definition.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sourceconfig-localdir"></a>`localDir` | [RepoRelativePath](#reporelativepath) | yes | Workspace-relative checkout or source directory. |
| <a id="sourceconfig-repository"></a>`repository` | [UrlString](#urlstring) \| None | no | Optional remote repository URL associated with this source. |
| <a id="sourceconfig-defaultbranch"></a>`defaultBranch` | [RefString](#refstring) \| None | no | Optional default branch or ref for this source. |
| <a id="sourceconfig-metadatafile"></a>`metadataFile` | [RepoRelativePath](#reporelativepath) \| None | no | Optional override for the component metadata file inside this source tree. |

<a id="supportstatusdefinition"></a>
### SupportStatusDefinition

Definition of one support-status vocabulary entry.

- category: `authored`
- ownership: `component-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportstatusdefinition-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="supportstatusdefinition-order"></a>`order` | int \| None | no | — |
| <a id="supportstatusdefinition-description"></a>`description` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="supportstatusdefinition-defaultmaintenancephase"></a>`defaultMaintenancePhase` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="supportwindow"></a>
### SupportWindow

Structured support-window metadata for a line or exact release.

- category: `authored`
- ownership: `consumer-owned`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportwindow-releasedate"></a>`releaseDate` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="supportwindow-maintenancephase"></a>`maintenancePhase` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="supportwindow-endofactivesupportdate"></a>`endOfActiveSupportDate` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="supportwindow-endofsupportdate"></a>`endOfSupportDate` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="supportwindow-endoflifedate"></a>`endOfLifeDate` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="supportwindow-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="supportwindow-notes"></a>`notes` | [NonEmptyString](#nonemptystring) \| None | no | — |

## Provider input types

Normalized provider snapshot contracts consumed by the pipeline.

<a id="providerasset"></a>
### ProviderAsset

Optional file-level metadata attached to a provider record.

- category: `provider`
- ownership: `provider-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerasset-name"></a>`name` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="providerasset-url"></a>`url` | [UrlString](#urlstring) | yes | — |
| <a id="providerasset-kind"></a>`kind` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerasset-mediatype"></a>`mediaType` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerasset-size"></a>`size` | [NonNegativeInteger](#nonnegativeinteger) \| None | no | — |
| <a id="providerasset-checksums"></a>`checksums` | dict[[Identifier](#identifier), [NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="providerasset-signatureurl"></a>`signatureUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="providerasset-sbomurl"></a>`sbomUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="providerasset-provenanceurl"></a>`provenanceUrl` | [UrlString](#urlstring) \| None | no | — |

<a id="providerdescriptor"></a>
### ProviderDescriptor

Descriptor for one loaded provider.

- category: `provider`
- ownership: `provider-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerdescriptor-key"></a>`key` | [ProviderKey](#providerkey) | yes | — |
| <a id="providerdescriptor-type"></a>`type` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="providerdescriptor-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerdescriptor-baseurl"></a>`baseUrl` | [ProviderBaseUrl](#providerbaseurl) \| None | no | — |
| <a id="providerdescriptor-fetchedat"></a>`fetchedAt` | [TimestampString](#timestampstring) | yes | — |

<a id="providerrecord"></a>
### ProviderRecord

Normalized release, candidate, or ref record from a provider.

- category: `provider`
- ownership: `provider-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerrecord-provider"></a>`provider` | [ProviderKey](#providerkey) | yes | — |
| <a id="providerrecord-kind"></a>`kind` | [RecordKind](#recordkind) | yes | — |
| <a id="providerrecord-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="providerrecord-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="providerrecord-sourcekey"></a>`sourceKey` | [SourceKey](#sourcekey) \| None | no | — |
| <a id="providerrecord-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-externalurl"></a>`externalUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="providerrecord-version"></a>`version` | [VersionString](#versionstring) \| None | no | — |
| <a id="providerrecord-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-tag"></a>`tag` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-ref"></a>`ref` | [RefString](#refstring) \| None | no | — |
| <a id="providerrecord-commitsha"></a>`commitSha` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="providerrecord-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) \| None | no | — |
| <a id="providerrecord-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-candidatesequence"></a>`candidateSequence` | [NonNegativeInteger](#nonnegativeinteger) \| None | no | — |
| <a id="providerrecord-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerrecord-createdat"></a>`createdAt` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="providerrecord-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="providerrecord-updatedat"></a>`updatedAt` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="providerrecord-urls"></a>`urls` | dict[[NonEmptyString](#nonemptystring), [UrlString](#urlstring)] \| None | no | — |
| <a id="providerrecord-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] \| None | no | — |

<a id="providersnapshotdocumentv1"></a>
### ProviderSnapshotDocumentV1

Provider-derived normalized snapshot from `site/provider-snapshot.json`.

- category: `provider`
- ownership: `provider-derived`
- file contract: `site/provider-snapshot.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providersnapshotdocumentv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | — |
| <a id="providersnapshotdocumentv1-providers"></a>`providers` | list[[ProviderDescriptor](#providerdescriptor)] | yes | — |
| <a id="providersnapshotdocumentv1-records"></a>`records` | list[[ProviderRecord](#providerrecord)] | yes | — |

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
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checkreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | — |
| <a id="checkreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | — |
| <a id="checkreportv1-command"></a>`command` | Literal['check'] | yes | — |
| <a id="checkreportv1-summary"></a>`summary` | [CheckSummary](#checksummary) | yes | — |
| <a id="checkreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | — |

<a id="checksummary"></a>
### CheckSummary

Outcome summary for one `check` run.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="checksummary-status"></a>`status` | [RunStatus](#runstatus) | yes | — |
| <a id="checksummary-passed"></a>`passed` | bool | yes | — |
| <a id="checksummary-failonseverity"></a>`failOnSeverity` | [CheckFailureThreshold](#checkfailurethreshold) | yes | — |
| <a id="checksummary-errorcount"></a>`errorCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | — |
| <a id="checksummary-warningcount"></a>`warningCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | — |
| <a id="checksummary-infocount"></a>`infoCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | — |

<a id="pipelinediagnosticentry"></a>
### PipelineDiagnosticEntry

Structured pipeline diagnostic entry.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinediagnosticentry-severity"></a>`severity` | [DiagnosticSeverity](#diagnosticseverity) | yes | — |
| <a id="pipelinediagnosticentry-code"></a>`code` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="pipelinediagnosticentry-message"></a>`message` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="pipelinediagnosticentry-componentslug"></a>`componentSlug` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinediagnosticentry-artifactkey"></a>`artifactKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinediagnosticentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinediagnosticentry-details"></a>`details` | [ReducedDiagnosticDetailsSummary](#reduceddiagnosticdetailssummary) \| [ExtensionsObject](#extensionsobject) \| None | no | — |

<a id="reduceddiagnosticdetailssummary"></a>
### ReducedDiagnosticDetailsSummary

Bounded replacement object for oversized diagnostic details.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="reduceddiagnosticdetailssummary-omitted"></a>`omitted` | Literal[True] | yes | — |
| <a id="reduceddiagnosticdetailssummary-reason"></a>`reason` | Literal['sizeLimitExceeded'] | yes | — |
| <a id="reduceddiagnosticdetailssummary-actualbytes"></a>`actualBytes` | [PositiveInteger](#positiveinteger) | yes | — |
| <a id="reduceddiagnosticdetailssummary-limitbytes"></a>`limitBytes` | [PositiveInteger](#positiveinteger) | yes | — |
| <a id="reduceddiagnosticdetailssummary-summary"></a>`summary` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="reduceddiagnosticdetailssummary-fingerprint"></a>`fingerprint` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="resolvedmaterializationentry"></a>
### ResolvedMaterializationEntry

One required local input discovered by planning.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationentry-sourcekey"></a>`sourceKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-inputkind"></a>`inputKind` | [MaterializationInputKind](#materializationinputkind) | yes | — |
| <a id="resolvedmaterializationentry-componentslug"></a>`componentSlug` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-artifactkey"></a>`artifactKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-version"></a>`version` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-ref"></a>`ref` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-tag"></a>`tag` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-commitsha"></a>`commitSha` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-expectedlocalpath"></a>`expectedLocalPath` | [LocalPathString](#localpathstring) | yes | — |
| <a id="resolvedmaterializationentry-status"></a>`status` | [MaterializationStatus](#materializationstatus) | yes | — |
| <a id="resolvedmaterializationentry-provenance"></a>`provenance` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="resolvedmaterializationentry-watcheligible"></a>`watchEligible` | bool \| None | no | — |
| <a id="resolvedmaterializationentry-reason"></a>`reason` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="resolvedmaterializationreportv1"></a>
### ResolvedMaterializationReportV1

Machine-readable planning report for required local inputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedmaterializationreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | — |
| <a id="resolvedmaterializationreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | — |
| <a id="resolvedmaterializationreportv1-target"></a>`target` | [PlanningTarget](#planningtarget) | yes | — |
| <a id="resolvedmaterializationreportv1-entries"></a>`entries` | list[[ResolvedMaterializationEntry](#resolvedmaterializationentry)] | yes | — |
| <a id="resolvedmaterializationreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | no | — |

<a id="stagedatafiles"></a>
### StageDataFiles

Inventory of aggregate metadata files present in a stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedatafiles-components"></a>`components` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="stagedatafiles-artifacts"></a>`artifacts` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="stagedatafiles-routes"></a>`routes` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="stagedatafiles-redirects"></a>`redirects` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="stagedatafiles-releases"></a>`releases` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-candidates"></a>`candidates` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-refs"></a>`refs` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-translations"></a>`translations` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-compatibility"></a>`compatibility` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-mounts"></a>`mounts` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-providers"></a>`providers` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-contentindex"></a>`contentIndex` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-diagnostics"></a>`diagnostics` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-unitcontributions"></a>`unitContributions` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-outputownership"></a>`outputOwnership` | [StageRelativePath](#stagerelativepath) \| None | no | — |
| <a id="stagedatafiles-aggregatedependencies"></a>`aggregateDependencies` | [StageRelativePath](#stagerelativepath) \| None | no | — |

<a id="stagemanifestv1"></a>
### StageManifestV1

Authoritative entry-point document for a staged output tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `manifest.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagemanifestv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | — |
| <a id="stagemanifestv1-stagelayoutversion"></a>`stageLayoutVersion` | [SchemaVersion](#schemaversion) | yes | — |
| <a id="stagemanifestv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | — |
| <a id="stagemanifestv1-command"></a>`command` | [StageCommand](#stagecommand) | yes | — |
| <a id="stagemanifestv1-frontmatterformat"></a>`frontMatterFormat` | Literal['yaml'] | yes | — |
| <a id="stagemanifestv1-aggregateformat"></a>`aggregateFormat` | Literal['json'] | yes | — |
| <a id="stagemanifestv1-roots"></a>`roots` | [StageRoots](#stageroots) | yes | — |
| <a id="stagemanifestv1-datafiles"></a>`dataFiles` | [StageDataFiles](#stagedatafiles) | yes | — |

<a id="stageroots"></a>
### StageRoots

Top-level directory roots within a stage tree.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stageroots-content"></a>`content` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="stageroots-static"></a>`static` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="stageroots-data"></a>`data` | [StageRelativePath](#stagerelativepath) | yes | — |

<a id="stagerunreportv1"></a>
### StageRunReportV1

Machine-readable result of `build` or one completed watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunreportv1-schemaversion"></a>`schemaVersion` | Literal[1] | yes | — |
| <a id="stagerunreportv1-generatedat"></a>`generatedAt` | [TimestampString](#timestampstring) | yes | — |
| <a id="stagerunreportv1-command"></a>`command` | [StageCommand](#stagecommand) | yes | — |
| <a id="stagerunreportv1-summary"></a>`summary` | [StageRunSummary](#stagerunsummary) | yes | — |
| <a id="stagerunreportv1-stagerootpath"></a>`stageRootPath` | [LocalPathString](#localpathstring) \| None | no | — |
| <a id="stagerunreportv1-manifestpath"></a>`manifestPath` | [LocalPathString](#localpathstring) \| None | no | — |
| <a id="stagerunreportv1-cycle"></a>`cycle` | [NonNegativeInteger](#nonnegativeinteger) \| None | no | — |
| <a id="stagerunreportv1-diagnostics"></a>`diagnostics` | list[[PipelineDiagnosticEntry](#pipelinediagnosticentry)] | yes | — |

<a id="stagerunsummary"></a>
### StageRunSummary

Outcome summary for one stage-producing run or watch cycle.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagerunsummary-status"></a>`status` | [RunStatus](#runstatus) | yes | — |
| <a id="stagerunsummary-succeeded"></a>`succeeded` | bool | yes | — |
| <a id="stagerunsummary-wrotestage"></a>`wroteStage` | bool | yes | — |
| <a id="stagerunsummary-stageusable"></a>`stageUsable` | bool | yes | — |
| <a id="stagerunsummary-errorcount"></a>`errorCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | — |
| <a id="stagerunsummary-warningcount"></a>`warningCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | — |
| <a id="stagerunsummary-infocount"></a>`infoCount` | [NonNegativeInteger](#nonnegativeinteger) | yes | — |

## Staged front matter types

Front matter and page-level metadata emitted into staged content.

<a id="artifactfrontmattersummary"></a>
### ArtifactFrontMatterSummary

Compact artifact summary embedded in component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactfrontmattersummary-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="artifactfrontmattersummary-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="artifactfrontmattersummary-lateststable"></a>`latestStable` | [VersionString](#versionstring) \| None | no | — |
| <a id="artifactfrontmattersummary-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] \| None | no | — |

<a id="pipelinecomponentfrontmatter"></a>
### PipelineComponentFrontMatter

Pipeline-owned component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinecomponentfrontmatter-slug"></a>`slug` | [Slug](#slug) | yes | — |
| <a id="pipelinecomponentfrontmatter-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinecomponentfrontmatter-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | — |
| <a id="pipelinecomponentfrontmatter-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] \| None | no | — |

<a id="pipelinefrontmatternamespace"></a>
### PipelineFrontMatterNamespace

Reserved top-level pipeline namespace emitted into staged pages.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinefrontmatternamespace-component"></a>`component` | [PipelineComponentFrontMatter](#pipelinecomponentfrontmatter) \| None | no | — |
| <a id="pipelinefrontmatternamespace-page"></a>`page` | [PipelinePageFrontMatter](#pipelinepagefrontmatter) \| None | no | — |

<a id="pipelinepagefrontmatter"></a>
### PipelinePageFrontMatter

Pipeline-owned page-local front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinepagefrontmatter-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="pipelinepagefrontmatter-section"></a>`section` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinepagefrontmatter-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) \| None | no | — |
| <a id="pipelinepagefrontmatter-path"></a>`path` | [PublicPath](#publicpath) | yes | — |
| <a id="pipelinepagefrontmatter-url"></a>`url` | [UrlString](#urlstring) | yes | — |
| <a id="pipelinepagefrontmatter-canonicalurl"></a>`canonicalUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="pipelinepagefrontmatter-alternateurls"></a>`alternateUrls` | list[[UrlString](#urlstring)] \| None | no | — |
| <a id="pipelinepagefrontmatter-locale"></a>`locale` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinepagefrontmatter-defaultlocale"></a>`defaultLocale` | bool \| None | no | — |
| <a id="pipelinepagefrontmatter-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="pipelinepagefrontmatter-translations"></a>`translations` | list[[TranslationLinkSummary](#translationlinksummary)] \| None | no | — |
| <a id="pipelinepagefrontmatter-componentpath"></a>`componentPath` | [PublicPath](#publicpath) | yes | — |
| <a id="pipelinepagefrontmatter-componenturl"></a>`componentUrl` | [UrlString](#urlstring) | yes | — |
| <a id="pipelinepagefrontmatter-version"></a>`version` | [VersionContext](#versioncontext) \| None | no | — |
| <a id="pipelinepagefrontmatter-provider"></a>`provider` | [ProviderProvenance](#providerprovenance) \| None | no | — |

<a id="providerprovenance"></a>
### ProviderProvenance

Compact provider provenance embedded in page front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerprovenance-key"></a>`key` | [ProviderKey](#providerkey) | yes | — |
| <a id="providerprovenance-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providerprovenance-externalurl"></a>`externalUrl` | [UrlString](#urlstring) \| None | no | — |

<a id="releaselinecontext"></a>
### ReleaseLineContext

Page-local release-line context.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselinecontext-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="releaselinecontext-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaselinecontext-ancestors"></a>`ancestors` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="releaselinecontext-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) \| None | no | — |

<a id="releaselinesummary"></a>
### ReleaseLineSummary

Compact release-line summary embedded into front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselinesummary-key"></a>`key` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="releaselinesummary-parent"></a>`parent` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaselinesummary-latest"></a>`latest` | [VersionString](#versionstring) \| None | no | — |
| <a id="releaselinesummary-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaselinesummary-headref"></a>`headRef` | [RefString](#refstring) \| None | no | — |
| <a id="releaselinesummary-aliases"></a>`aliases` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="releaselinesummary-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) \| None | no | — |

<a id="resolvedorigin"></a>
### ResolvedOrigin

Resolved publication origin information.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedorigin-key"></a>`key` | [OriginKey](#originkey) | yes | — |
| <a id="resolvedorigin-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | — |
| <a id="resolvedorigin-hostname"></a>`hostname` | [HostnameString](#hostnamestring) | yes | — |

<a id="resolvedpathset"></a>
### ResolvedPathSet

Resolved public paths for one component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedpathset-component"></a>`component` | [PublicPath](#publicpath) | yes | — |
| <a id="resolvedpathset-development"></a>`development` | [PublicPath](#publicpath) | yes | — |
| <a id="resolvedpathset-docs"></a>`docs` | [PublicPath](#publicpath) | yes | — |
| <a id="resolvedpathset-assets"></a>`assets` | [PublicPath](#publicpath) | yes | — |

<a id="resolvedpublication"></a>
### ResolvedPublication

Resolved route and URL bundle for one component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedpublication-origin"></a>`origin` | [ResolvedOrigin](#resolvedorigin) | yes | — |
| <a id="resolvedpublication-paths"></a>`paths` | [ResolvedPathSet](#resolvedpathset) | yes | — |
| <a id="resolvedpublication-urls"></a>`urls` | [ResolvedUrlSet](#resolvedurlset) | yes | — |

<a id="resolvedurlset"></a>
### ResolvedUrlSet

Resolved fully qualified URLs for one component.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="resolvedurlset-component"></a>`component` | [UrlString](#urlstring) | yes | — |
| <a id="resolvedurlset-development"></a>`development` | [UrlString](#urlstring) | yes | — |
| <a id="resolvedurlset-docs"></a>`docs` | [UrlString](#urlstring) | yes | — |
| <a id="resolvedurlset-assets"></a>`assets` | [UrlString](#urlstring) | yes | — |

<a id="translationlinksummary"></a>
### TranslationLinkSummary

Compact translation sibling reference.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="translationlinksummary-locale"></a>`locale` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="translationlinksummary-path"></a>`path` | [PublicPath](#publicpath) \| None | no | — |
| <a id="translationlinksummary-url"></a>`url` | [UrlString](#urlstring) | yes | — |
| <a id="translationlinksummary-title"></a>`title` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="versioncontext"></a>
### VersionContext

Version or ref context attached to one staged page.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="versioncontext-kind"></a>`kind` | [RecordKind](#recordkind) | yes | — |
| <a id="versioncontext-label"></a>`label` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="versioncontext-path"></a>`path` | [PublicPath](#publicpath) \| None | no | — |
| <a id="versioncontext-url"></a>`url` | [UrlString](#urlstring) \| None | no | — |
| <a id="versioncontext-docspath"></a>`docsPath` | [PublicPath](#publicpath) \| None | no | — |
| <a id="versioncontext-docsurl"></a>`docsUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="versioncontext-tag"></a>`tag` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="versioncontext-ref"></a>`ref` | [RefString](#refstring) \| None | no | — |
| <a id="versioncontext-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="versioncontext-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) \| None | no | — |
| <a id="versioncontext-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="versioncontext-candidatesequence"></a>`candidateSequence` | int \| None | no | — |
| <a id="versioncontext-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="versioncontext-releaseline"></a>`releaseLine` | [ReleaseLineContext](#releaselinecontext) \| None | no | — |
| <a id="versioncontext-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) \| None | no | — |

## Staged aggregate metadata types

Public aggregate JSON contracts emitted under `data/`.

<a id="artifactsdataentry"></a>
### ArtifactsDataEntry

Entry in `data/artifacts.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactsdataentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="artifactsdataentry-key"></a>`key` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="artifactsdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="artifactsdataentry-sourcekey"></a>`sourceKey` | [SourceKey](#sourcekey) \| None | no | — |
| <a id="artifactsdataentry-docsroot"></a>`docsRoot` | [RepoRelativePath](#reporelativepath) \| None | no | — |
| <a id="artifactsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](#providerkey)] \| None | no | — |
| <a id="artifactsdataentry-versioning"></a>`versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) \| None | no | — |
| <a id="artifactsdataentry-lateststable"></a>`latestStable` | [VersionString](#versionstring) \| None | no | — |
| <a id="artifactsdataentry-latestrelease"></a>`latestRelease` | [LatestReleaseSummary](#latestreleasesummary) \| None | no | — |
| <a id="artifactsdataentry-latestcandidate"></a>`latestCandidate` | [LatestCandidateSummary](#latestcandidatesummary) \| None | no | — |
| <a id="artifactsdataentry-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] \| None | no | — |
| <a id="artifactsdataentry-namedrefs"></a>`namedRefs` | list[[RefAggregateEntry](#refaggregateentry)] \| None | no | — |
| <a id="artifactsdataentry-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[NonEmptyString](#nonemptystring), [SupportStatusDefinition](#supportstatusdefinition)] \| None | no | — |
| <a id="artifactsdataentry-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](#urlstring) \| None | no | — |

<a id="candidateaggregateentry"></a>
### CandidateAggregateEntry

Entry in `data/candidates.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="candidateaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) \| None | no | — |
| <a id="candidateaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="candidateaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="candidateaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="candidateaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="candidateaggregateentry-version"></a>`version` | [VersionString](#versionstring) | yes | — |
| <a id="candidateaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="candidateaggregateentry-candidatesequence"></a>`candidateSequence` | int \| None | no | — |
| <a id="candidateaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="candidateaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="candidateaggregateentry-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="candidateaggregateentry-createdat"></a>`createdAt` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="candidateaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="candidateaggregateentry-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] \| None | no | — |

<a id="compatibilityaggregateentry"></a>
### CompatibilityAggregateEntry

Entry in `data/compatibility.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="compatibilityaggregateentry-subjectid"></a>`subjectId` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="compatibilityaggregateentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="compatibilityaggregateentry-relation"></a>`relation` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="compatibilityaggregateentry-scope"></a>`scope` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="compatibilityaggregateentry-confidence"></a>`confidence` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="compatibilityaggregateentry-notes"></a>`notes` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="compatibilityaggregateentry-evidence"></a>`evidence` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |

<a id="componentsdataentry"></a>
### ComponentsDataEntry

Entry in `data/components.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentsdataentry-slug"></a>`slug` | [Slug](#slug) | yes | — |
| <a id="componentsdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="componentsdataentry-weight"></a>`weight` | int \| None | no | Optional ordering hint copied from the authored catalog for consumer-rendered component lists. |
| <a id="componentsdataentry-group"></a>`group` | [Identifier](#identifier) \| None | no | — |
| <a id="componentsdataentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | — |
| <a id="componentsdataentry-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | — |
| <a id="componentsdataentry-providerkeys"></a>`providerKeys` | list[[ProviderKey](#providerkey)] \| None | no | — |
| <a id="componentsdataentry-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] \| None | no | — |

<a id="contentindexentry"></a>
### ContentIndexEntry

Entry in `data/content-index.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="contentindexentry-id"></a>`id` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="contentindexentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="contentindexentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) \| None | no | — |
| <a id="contentindexentry-pagekind"></a>`pageKind` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="contentindexentry-section"></a>`section` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | — |
| <a id="contentindexentry-path"></a>`path` | [PublicPath](#publicpath) | yes | — |
| <a id="contentindexentry-url"></a>`url` | [UrlString](#urlstring) | yes | — |
| <a id="contentindexentry-canonicalurl"></a>`canonicalUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="contentindexentry-title"></a>`title` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-linktitle"></a>`linkTitle` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-description"></a>`description` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-summary"></a>`summary` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-weight"></a>`weight` | int \| None | no | — |
| <a id="contentindexentry-parentid"></a>`parentId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-ancestorids"></a>`ancestorIds` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="contentindexentry-sourcepath"></a>`sourcePath` | [RepoRelativePath](#reporelativepath) \| None | no | — |
| <a id="contentindexentry-versionkind"></a>`versionKind` | [RecordKind](#recordkind) \| None | no | — |
| <a id="contentindexentry-versionlabel"></a>`versionLabel` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) \| None | no | — |
| <a id="contentindexentry-locale"></a>`locale` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-defaultlocale"></a>`defaultLocale` | bool \| None | no | — |
| <a id="contentindexentry-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-provider"></a>`provider` | [ProviderKey](#providerkey) \| None | no | — |
| <a id="contentindexentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="contentindexentry-candidatesequence"></a>`candidateSequence` | int \| None | no | — |
| <a id="contentindexentry-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="latestcandidatesummary"></a>
### LatestCandidateSummary

Compact latest-candidate summary embedded in artifact aggregates.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="latestcandidatesummary-version"></a>`version` | [VersionString](#versionstring) \| None | no | — |
| <a id="latestcandidatesummary-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="latestcandidatesummary-candidatesequence"></a>`candidateSequence` | int \| None | no | — |
| <a id="latestcandidatesummary-votestatus"></a>`voteStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="latestreleasesummary"></a>
### LatestReleaseSummary

Compact latest-release summary embedded in artifact aggregates.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="latestreleasesummary-version"></a>`version` | [VersionString](#versionstring) | yes | — |
| <a id="latestreleasesummary-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="latestreleasesummary-tag"></a>`tag` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="latestreleasesummary-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) \| None | no | — |
| <a id="latestreleasesummary-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) \| None | no | — |

<a id="mountaggregateentry"></a>
### MountAggregateEntry

Entry in `data/mounts.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountaggregateentry-mountid"></a>`mountId` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="mountaggregateentry-ownerid"></a>`ownerId` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="mountaggregateentry-kind"></a>`kind` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="mountaggregateentry-trustclass"></a>`trustClass` | [TrustClass](#trustclass) | yes | — |
| <a id="mountaggregateentry-publicpath"></a>`publicPath` | [PublicPath](#publicpath) | yes | — |
| <a id="mountaggregateentry-sourceref"></a>`sourceRef` | [MountSourceRef](#mountsourceref) | yes | — |
| <a id="mountaggregateentry-versioncontext"></a>`versionContext` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="mountaggregateentry-indexbehavior"></a>`indexBehavior` | [IndexBehavior](#indexbehavior) \| None | no | — |
| <a id="mountaggregateentry-metadata"></a>`metadata` | [ExtensionsObject](#extensionsobject) \| None | no | — |

<a id="providersdataentry"></a>
### ProvidersDataEntry

Entry in `data/providers.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providersdataentry-key"></a>`key` | [ProviderKey](#providerkey) | yes | — |
| <a id="providersdataentry-type"></a>`type` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="providersdataentry-displayname"></a>`displayName` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="providersdataentry-baseurl"></a>`baseUrl` | [ProviderBaseUrl](#providerbaseurl) \| None | no | — |
| <a id="providersdataentry-fetchedat"></a>`fetchedAt` | [TimestampString](#timestampstring) | yes | — |

<a id="redirectaggregateentry"></a>
### RedirectAggregateEntry

Entry in `data/redirects.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="redirectaggregateentry-fromurl"></a>`fromUrl` | [UrlString](#urlstring) | yes | — |
| <a id="redirectaggregateentry-tourl"></a>`toUrl` | [UrlString](#urlstring) | yes | — |
| <a id="redirectaggregateentry-status"></a>`status` | int | yes | — |
| <a id="redirectaggregateentry-reason"></a>`reason` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="redirectaggregateentry-sourcekind"></a>`sourceKind` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="refaggregateentry"></a>
### RefAggregateEntry

Entry in `data/refs.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="refaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) \| None | no | — |
| <a id="refaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="refaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="refaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="refaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="refaggregateentry-kind"></a>`kind` | [RecordKind](#recordkind) | yes | — |
| <a id="refaggregateentry-namedrefkey"></a>`namedRefKey` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="refaggregateentry-ref"></a>`ref` | [RefString](#refstring) | yes | — |
| <a id="refaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="refaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="refaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="releaseaggregateentry"></a>
### ReleaseAggregateEntry

Entry in `data/releases.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaseaggregateentry-provider"></a>`provider` | [ProviderKey](#providerkey) \| None | no | — |
| <a id="releaseaggregateentry-externalid"></a>`externalId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaseaggregateentry-externalurl"></a>`externalUrl` | [UrlString](#urlstring) \| None | no | — |
| <a id="releaseaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="releaseaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) | yes | — |
| <a id="releaseaggregateentry-version"></a>`version` | [VersionString](#versionstring) | yes | — |
| <a id="releaseaggregateentry-displayversion"></a>`displayVersion` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaseaggregateentry-tag"></a>`tag` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaseaggregateentry-releaseline"></a>`releaseLine` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaseaggregateentry-releaselineancestors"></a>`releaseLineAncestors` | list[[NonEmptyString](#nonemptystring)] \| None | no | — |
| <a id="releaseaggregateentry-supportstatus"></a>`supportStatus` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaseaggregateentry-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) \| None | no | — |
| <a id="releaseaggregateentry-publicationstate"></a>`publicationState` | [PublicationState](#publicationstate) \| None | no | — |
| <a id="releaseaggregateentry-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](#withdrawalbehavior) \| None | no | — |
| <a id="releaseaggregateentry-redirecttarget"></a>`redirectTarget` | [ReferenceString](#referencestring) \| [UrlString](#urlstring) \| None | no | — |
| <a id="releaseaggregateentry-maturity"></a>`maturity` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="releaseaggregateentry-publishedat"></a>`publishedAt` | [TimestampString](#timestampstring) \| None | no | — |
| <a id="releaseaggregateentry-assets"></a>`assets` | list[[ProviderAsset](#providerasset)] \| None | no | — |
| <a id="releaseaggregateentry-urls"></a>`urls` | dict[[NonEmptyString](#nonemptystring), [UrlString](#urlstring)] \| None | no | — |

<a id="routeaggregateentry"></a>
### RouteAggregateEntry

Entry in `data/routes.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="routeaggregateentry-originkey"></a>`originKey` | [OriginKey](#originkey) | yes | — |
| <a id="routeaggregateentry-baseurl"></a>`baseUrl` | [UrlString](#urlstring) | yes | — |
| <a id="routeaggregateentry-path"></a>`path` | [PublicPath](#publicpath) | yes | — |
| <a id="routeaggregateentry-url"></a>`url` | [UrlString](#urlstring) | yes | — |
| <a id="routeaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="routeaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) \| None | no | — |
| <a id="routeaggregateentry-section"></a>`section` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="routeaggregateentry-canonical"></a>`canonical` | bool \| None | no | — |
| <a id="routeaggregateentry-routekind"></a>`routeKind` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="routeaggregateentry-targetid"></a>`targetId` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="routeaggregateentry-label"></a>`label` | [NonEmptyString](#nonemptystring) \| None | no | — |
| <a id="routeaggregateentry-locale"></a>`locale` | [NonEmptyString](#nonemptystring) \| None | no | — |

<a id="translationsetaggregateentry"></a>
### TranslationSetAggregateEntry

Entry in `data/translations.json`.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="translationsetaggregateentry-translationkey"></a>`translationKey` | [NonEmptyString](#nonemptystring) | yes | — |
| <a id="translationsetaggregateentry-componentslug"></a>`componentSlug` | [Slug](#slug) | yes | — |
| <a id="translationsetaggregateentry-artifactkey"></a>`artifactKey` | [ArtifactKey](#artifactkey) \| None | no | — |
| <a id="translationsetaggregateentry-entries"></a>`entries` | list[[TranslationLinkSummary](#translationlinksummary)] | yes | — |

## Incremental bookkeeping types

Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`.

<a id="aggregatedependencyentryv1"></a>
### AggregateDependencyEntryV1

One coordinator-owned aggregate and the units that may change its payload.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="aggregatedependencyentryv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](#stagerelativepath) | yes | — |
| <a id="aggregatedependencyentryv1-dependentunitids"></a>`dependentUnitIds` | tuple[str, ...] | no | — |

<a id="aggregatedependencymapv1"></a>
### AggregateDependencyMapV1

Shared-output dependency map for the current first-wave coordinator outputs.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/aggregate-dependencies.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="aggregatedependencymapv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | — |
| <a id="aggregatedependencymapv1-entries"></a>`entries` | tuple[[AggregateDependencyEntryV1](#aggregatedependencyentryv1), ...] | no | — |

<a id="outputownershipclaimv1"></a>
### OutputOwnershipClaimV1

One exact published file or directory root together with its logical owner.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: —

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="outputownershipclaimv1-ownerid"></a>`ownerId` | str | yes | — |
| <a id="outputownershipclaimv1-unitid"></a>`unitId` | str \| None | no | — |
| <a id="outputownershipclaimv1-pathkind"></a>`pathKind` | Literal['directory', 'file'] | yes | — |
| <a id="outputownershipclaimv1-stagerelativepath"></a>`stageRelativePath` | [StageRelativePath](#stagerelativepath) | yes | — |

<a id="outputownershipmapv1"></a>
### OutputOwnershipMapV1

Published ownership inventory used to prune retained stages safely.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/output-ownership.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="outputownershipmapv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | — |
| <a id="outputownershipmapv1-claims"></a>`claims` | tuple[[OutputOwnershipClaimV1](#outputownershipclaimv1), ...] | no | — |

<a id="persistedunitcontributionsv1"></a>
### PersistedUnitContributionsV1

Stable per-unit page contribution manifests retained in the visible stage.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: `data/_pipeline/unit-contributions.json`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="persistedunitcontributionsv1-schemaversion"></a>`schemaVersion` | Literal[1] | no | — |
| <a id="persistedunitcontributionsv1-units"></a>`units` | tuple[[UnitContributionManifestWire](#unitcontributionmanifestwire), ...] | no | — |

<a id="stagedpagecontributionwire"></a>
### StagedPageContributionWire

Metadata emitted by one page-staging worker for later aggregation.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="stagedpagecontributionwire-stagerelativepath"></a>`stageRelativePath` | str | yes | — |
| <a id="stagedpagecontributionwire-componentslug"></a>`componentSlug` | str | yes | — |
| <a id="stagedpagecontributionwire-artifactkey"></a>`artifactKey` | str \| None | no | — |
| <a id="stagedpagecontributionwire-section"></a>`section` | str | yes | — |
| <a id="stagedpagecontributionwire-pagekind"></a>`pageKind` | str | yes | — |
| <a id="stagedpagecontributionwire-publicpath"></a>`publicPath` | str | yes | — |
| <a id="stagedpagecontributionwire-publicurl"></a>`publicUrl` | str \| None | no | — |
| <a id="stagedpagecontributionwire-componentpath"></a>`componentPath` | str | yes | — |
| <a id="stagedpagecontributionwire-componenturl"></a>`componentUrl` | str \| None | no | — |
| <a id="stagedpagecontributionwire-originkey"></a>`originKey` | str | yes | — |
| <a id="stagedpagecontributionwire-versioncontext"></a>`versionContext` | dict[str, object] \| None | no | — |
| <a id="stagedpagecontributionwire-versionkind"></a>`versionKind` | str \| None | no | — |
| <a id="stagedpagecontributionwire-versionref"></a>`versionRef` | str \| None | no | — |
| <a id="stagedpagecontributionwire-version"></a>`version` | str \| None | no | — |
| <a id="stagedpagecontributionwire-locale"></a>`locale` | str \| None | no | — |
| <a id="stagedpagecontributionwire-defaultlocale"></a>`defaultLocale` | bool | no | — |
| <a id="stagedpagecontributionwire-translationkey"></a>`translationKey` | str \| None | no | — |
| <a id="stagedpagecontributionwire-title"></a>`title` | str \| None | no | — |
| <a id="stagedpagecontributionwire-linktitle"></a>`linkTitle` | str \| None | no | — |
| <a id="stagedpagecontributionwire-sourcepath"></a>`sourcePath` | str | yes | — |
| <a id="stagedpagecontributionwire-canonicalurl"></a>`canonicalUrl` | str \| None | no | — |

<a id="unitcontributionmanifestwire"></a>
### UnitContributionManifestWire

Worker-emitted contribution fragment consumed by the coordinator.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="unitcontributionmanifestwire-unitid"></a>`unitId` | str | yes | — |
| <a id="unitcontributionmanifestwire-pages"></a>`pages` | tuple[[StagedPageContributionWire](#stagedpagecontributionwire), ...] | no | — |

