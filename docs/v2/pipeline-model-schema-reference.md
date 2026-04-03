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

This document is a typed reference for the publication, lifecycle,
relationship, and provider-integration model. It is intentionally more explicit
than the narrative docs: each model type is listed with fields, field types, and
a short description.

It remains a design reference rather than an implementation-locked schema.

## Scope and conventions

- examples elsewhere may use YAML for readability, but aggregate staged metadata
  is assumed to use JSON as the interoperability baseline
- `?` means optional
- `[]` means list/array
- `Map<K, V>` means a string-keyed object map
- `Enum<...>` means a constrained string set
- links in type positions point to other types defined in this document

## Type index

### Authored input types

- [ComponentRepositoryDocument](#componentrepositorydocument)
- [ComponentIdentity](#componentidentity)
- [ContentRoots](#contentroots)
- [ComponentLifecycleHints](#componentlifecyclehints)
- [CatalogDocument](#catalogdocument)
- [CatalogDefaults](#catalogdefaults)
- [PublicationDefaults](#publicationdefaults)
- [LocalizationConfig](#localizationconfig)
- [OriginConfig](#originconfig)
- [SourceConfig](#sourceconfig)
- [GroupConfig](#groupconfig)
- [ComponentCatalogEntry](#componentcatalogentry)
- [ComponentContentSelection](#componentcontentselection)
- [PublicationConfig](#publicationconfig)
- [RouteAliasConfig](#routealiasconfig)
- [RedirectRuleConfig](#redirectruleconfig)
- [ArtifactConfig](#artifactconfig)
- [ArtifactVersioningConfig](#artifactversioningconfig)
- [NamedRefConfig](#namedrefconfig)
- [PublicationSelectionPolicy](#publicationselectionpolicy)
- [LineHeadSelectionPolicy](#lineheadselectionpolicy)
- [ReleaseSelectionPolicy](#releaseselectionpolicy)
- [CandidateSelectionPolicy](#candidateselectionpolicy)
- [ArtifactLifecycleConfig](#artifactlifecycleconfig)
- [ExactReleaseConfig](#exactreleaseconfig)
- [MountConfig](#mountconfig)
- [CompatibilityAssertionConfig](#compatibilityassertionconfig)
- [ReleaseLineConfig](#releaselineconfig)
- [SupportStatusDefinition](#supportstatusdefinition)
- [SupportWindow](#supportwindow)
- [PageTranslationMetadata](#pagetranslationmetadata)

### Provider input types

- [ProviderSnapshot](#providersnapshot)
- [ProviderDescriptor](#providerdescriptor)
- [ProviderRecord](#providerrecord)
- [ProviderAsset](#providerasset)

### Planning and stage-contract types

- [ResolvedMaterializationReport](#resolvedmaterializationreport)
- [ResolvedMaterializationEntry](#resolvedmaterializationentry)
- [StageManifest](#stagemanifest)
- [StageRoots](#stageroots)
- [StageDataFiles](#stagedatafiles)
- [StageDiagnosticEntry](#stagediagnosticentry)

### Staged front matter types

- [SitePipelineComponentFrontMatter](#sitepipelinecomponentfrontmatter)
- [ResolvedPublication](#resolvedpublication)
- [ResolvedOrigin](#resolvedorigin)
- [ResolvedPathSet](#resolvedpathset)
- [ResolvedUrlSet](#resolvedurlset)
- [ArtifactFrontMatterSummary](#artifactfrontmattersummary)
- [ReleaseLineSummary](#releaselinesummary)
- [SitePipelineComponentPageFrontMatter](#sitepipelinecomponentpagefrontmatter)
- [VersionContext](#versioncontext)
- [ReleaseLineContext](#releaselinecontext)
- [TranslationLinkSummary](#translationlinksummary)
- [ProviderProvenance](#providerprovenance)

### Staged aggregate metadata types

- [ProvidersDataEntry](#providersdataentry)
- [ComponentsDataEntry](#componentsdataentry)
- [ArtifactsDataEntry](#artifactsdataentry)
- [ReleaseAggregateEntry](#releaseaggregateentry)
- [CandidateAggregateEntry](#candidateaggregateentry)
- [RefAggregateEntry](#refaggregateentry)
- [RouteAggregateEntry](#routeaggregateentry)
- [RedirectAggregateEntry](#redirectaggregateentry)
- [TranslationSetAggregateEntry](#translationsetaggregateentry)
- [CompatibilityAggregateEntry](#compatibilityaggregateentry)
- [MountAggregateEntry](#mountaggregateentry)
- [ContentIndexEntry](#contentindexentry)
- [LatestReleaseSummary](#latestreleasesummary)
- [LatestCandidateSummary](#latestcandidatesummary)

## Scalar and helper types

| Type | Base type | Description |
| --- | --- | --- |
| `Identifier` | `String` | Non-empty symbolic key. |
| `Slug` | `String` | Stable component identifier. |
| `ArtifactKey` | `String` | Stable artifact identifier unique within a component. |
| `OriginKey` | `String` | Key for a publication origin. |
| `SourceKey` | `String` | Key for a source/repository entry. |
| `ProviderKey` | `String` | Key for a provider descriptor. |
| `VersionString` | `String` | Exact version string such as `4.0.0`. |
| `RefString` | `String` | Moving ref name such as `main` or `releases/4.x`. |
| `RegexString` | `String` | Regex pattern stored as text. |
| `RepoRelativePath` | `String` | Repository-relative path such as `site/docs` or `docs/runtime`. |
| `LocalPathString` | `String` | Consumer-local filesystem path used during staging or materialization. |
| `MountSourceRef` | `String` | Stable mount source reference such as a path, generator output key, or bundle identifier. |
| `PublicPath` | `String` | Resolved public path such as `/development/docs/`. |
| `StageRelativePath` | `String` | Stage-root-relative path such as `data/routes.json`. |
| `UrlString` | `String` | Absolute URL such as `https://spark.example.org/`. |
| `HostnameString` | `String` | Hostname derived from an origin URL. |
| `TimestampString` | `String` | RFC 3339 / ISO 8601 timestamp string. |
| `ExtensionsObject` | `Object` | Provider-specific opaque structured metadata. |

## Shared enums

| Type | Values | Description |
| --- | --- | --- |
| `RecordKind` | `development`, `named-ref`, `line-head`, `candidate`, `released` | Normalized lifecycle category for provider records and version contexts. |
| `MaterializationStatus` | `present`, `missing`, `stale`, `unresolved` | Whether a required local input is ready for staging. |
| `PublicationState` | `published`, `hidden`, `withdrawn`, `tombstoned` | Public visibility and route-preservation state for an exact release. |
| `WithdrawalBehavior` | `notice`, `redirect`, `omit` | How withdrawn or tombstoned releases are surfaced when they are not published normally. |
| `LineHeadSelectionMode` | `none`, `all-authored`, `explicit` | How line-head contexts are selected for staging. |
| `ReleaseSelectionMode` | `latest-per-line`, `latest-n`, `all-known`, `explicit` | How exact releases are selected for staging. |
| `CandidateSelectionMode` | `none`, `latest`, `explicit` | How release candidates are selected for staging. |
| `IndexBehavior` | `full`, `metadata-only`, `none` | How mounted content participates in indexing and search. |
| `DiagnosticSeverity` | `info`, `warning`, `error` | Severity level for pipeline diagnostics. |

<a id="componentrepositorydocument"></a>
## ComponentRepositoryDocument

Component-owned metadata from `site/component.yaml`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `schemaVersion` | `Integer` | yes | Schema version for the component metadata file. |
| `component` | [ComponentIdentity](#componentidentity) | yes | Stable component identity. |
| `content` | [ContentRoots](#contentroots) | no | Repository-owned content root hints. |
| `lifecycle` | [ComponentLifecycleHints](#componentlifecyclehints) | no | Optional high-level lifecycle hints or defaults. |

<a id="componentidentity"></a>
## ComponentIdentity

Stable identity fields for a component repository.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `slug` | `Slug` | yes | Stable internal component identifier. |
| `displayName` | `String` | no | Human-readable component name. |

<a id="contentroots"></a>
## ContentRoots

Repository-relative locations of authored content.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `pagesRoot` | `RepoRelativePath` | no | Root for non-versioned component pages. |
| `docsRoot` | `RepoRelativePath` | no | Root for versioned documentation content. |
| `assetsRoot` | `RepoRelativePath` | no | Root for static assets. |

<a id="componentlifecyclehints"></a>
## ComponentLifecycleHints

Optional component-level lifecycle defaults. Artifact-level lifecycle remains the
main source of truth when artifacts are present.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `latestStable` | `VersionString` | no | Optional convenience hint for the latest stable version. |
| `supportStatusVocabulary` | `Map<String, [SupportStatusDefinition](#supportstatusdefinition)>` | no | Optional default support-status vocabulary inherited by artifacts. |

<a id="catalogdocument"></a>
## CatalogDocument

Consumer-owned catalog, typically `site/components.yaml`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `schemaVersion` | `Integer` | yes | Schema version for the catalog format. |
| `defaults` | [CatalogDefaults](#catalogdefaults) | no | Shared default settings. |
| `origins` | `Map<OriginKey, [OriginConfig](#originconfig)>` | no | Named publication origins. |
| `sources` | `Map<SourceKey, [SourceConfig](#sourceconfig)>` | no | Named repository/source definitions. |
| `groups` | `Map<Identifier, [GroupConfig](#groupconfig)>` | no | Optional grouping defaults for components. |
| `components` | Array<[ComponentCatalogEntry](#componentcatalogentry)> | yes | Participating components. |

<a id="catalogdefaults"></a>
## CatalogDefaults

Shared defaults applied before per-component overrides.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `metadataFile` | `RepoRelativePath` | no | Default location of the component metadata file. |
| `pagesRoot` | `RepoRelativePath` | no | Default non-versioned pages root. |
| `docsRoot` | `RepoRelativePath` | no | Default docs root. |
| `assetsRoot` | `RepoRelativePath` | no | Default assets root. |
| `publication` | [PublicationDefaults](#publicationdefaults) | no | Shared publication defaults. |
| `localization` | [LocalizationConfig](#localizationconfig) | no | Shared locale and translation defaults. |

<a id="publicationdefaults"></a>
## PublicationDefaults

Default routing segments used to derive publication paths.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `origin` | `OriginKey` | no | Default origin for components that do not override it. |
| `developmentSegment` | `String` | no | Segment appended to the component mount for development content. |
| `docsSegment` | `String` | no | Segment appended under the development path for docs. |
| `assetsSegment` | `String` | no | Segment appended under the development path for assets. |

<a id="localizationconfig"></a>
## LocalizationConfig

Locale and translation defaults.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `defaultLocale` | `String` | no | Default site or component locale such as `en`. |
| `supportedLocales` | `String[]` | no | Set of locales intended for publication. |
| `routeMode` | `String` | no | Locale routing mode such as `none`, `prefix-all`, `prefix-nondefault`, or `origin-per-locale`. |
| `fallbackLocale` | `String` | no | Locale used when a page does not have a translated sibling. |

<a id="originconfig"></a>
## OriginConfig

Named publication origin.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `baseUrl` | `UrlString` | yes | Absolute base URL for the origin. |
| `canonical` | `Boolean` | no | Whether this origin is the canonical publication origin. |
| `localeBaseUrls` | `Map<String, UrlString>` | no | Optional locale-specific base URL overrides for host-per-locale publication. |
| `labels` | `String[]` | no | Optional human-oriented labels for UI or diagnostics. |

<a id="sourceconfig"></a>
## SourceConfig

Repository or checkout definition.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `localDir` | `RepoRelativePath` | yes | Local checkout location relative to the consumer workspace. |
| `repository` | `UrlString` | no | Optional remote repository URL. |
| `defaultBranch` | `RefString` | no | Default branch/ref for source resolution. |
| `metadataFile` | `RepoRelativePath` | no | Override for the component metadata file within this source. |

<a id="groupconfig"></a>
## GroupConfig

Reusable defaults for a set of components.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `displayName` | `String` | no | Human-readable group name. |
| `pathPrefix` | `PublicPath` | no | Shared public path prefix for grouped components. |
| `navigationSection` | `String` | no | Optional renderer-facing navigation grouping label. |
| `weight` | `Integer` | no | Optional ordering hint. |
| `publication` | [PublicationConfig](#publicationconfig) | no | Group-level publication defaults, usually origin-related. |

<a id="componentcatalogentry"></a>
## ComponentCatalogEntry

One component entry in the consumer catalog.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `slug` | `Slug` | yes | Stable component identifier. |
| `displayName` | `String` | no | Human-readable component name override or convenience value. |
| `localDir` | `RepoRelativePath` | no | Simple shorthand for local checkout binding in small setups. |
| `group` | `Identifier` | no | Group key for inherited defaults. |
| `content` | [ComponentContentSelection](#componentcontentselection) | no | Shared content source selection. |
| `publication` | [PublicationConfig](#publicationconfig) | no | Explicit publication configuration. |
| `publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) | no | Default version-context selection policy inherited by contained artifacts unless they override it. |
| `localization` | [LocalizationConfig](#localizationconfig) | no | Component-specific localization overrides. |
| `compatibility` | Array<[CompatibilityAssertionConfig](#compatibilityassertionconfig)> | no | Component-level compatibility assertions. |
| `mounts` | Array<[MountConfig](#mountconfig)> | no | Component-level generated or imported documentation mounts. |
| `artifacts` | Array<[ArtifactConfig](#artifactconfig)> | no | Independently versioned artifacts for the component. |

<a id="componentcontentselection"></a>
## ComponentContentSelection

Selection of the source that owns shared component content.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `source` | `SourceKey` | no | Source key for shared landing pages or docs roots. |

<a id="publicationconfig"></a>
## PublicationConfig

Explicit publication configuration or inherited publication defaults.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `origin` | `OriginKey` | no | Resolved or resolvable origin key. |
| `pathSegment` | `String` | no | Relative segment used with a group path prefix. |
| `mountPath` | `PublicPath` | no | Component mount path under the resolved origin. |
| `componentPath` | `PublicPath` | no | Fully explicit component home path override. |
| `developmentPath` | `PublicPath` | no | Fully explicit development path override. |
| `docsPath` | `PublicPath` | no | Fully explicit docs path override. |
| `assetsPath` | `PublicPath` | no | Fully explicit assets path override. |
| `canonicalPath` | `PublicPath` | no | Preferred canonical path when it differs from the derived route. |
| `aliases` | Array<[RouteAliasConfig](#routealiasconfig)> | no | Additional non-redirecting routes for the same published target. |
| `redirects` | Array<[RedirectRuleConfig](#redirectruleconfig)> | no | Redirect routes to generate for legacy or moving paths. |

<a id="routealiasconfig"></a>
## RouteAliasConfig

Additional route resolving to the same published target.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `path` | `PublicPath` | yes | Alias path under the resolved or overridden origin. |
| `origin` | `OriginKey` | no | Optional origin override for the alias. |
| `label` | `String` | no | Optional human-facing label such as `latest`. |

<a id="redirectruleconfig"></a>
## RedirectRuleConfig

Authored redirect rule resolved by the pipeline into deployment-neutral redirect metadata.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `fromPath` | `PublicPath` | yes | Source path for the redirect. |
| `fromOrigin` | `OriginKey` | no | Optional origin override for the redirect source. |
| `target` | `String` | yes | Internal route reference or fully qualified destination URL using an allowed scheme. |
| `status` | `Integer` | no | Redirect status such as `301`, `302`, `307`, or `308`. |
| `reason` | `String` | no | Optional human-facing explanation or operator note. |

<a id="artifactconfig"></a>
## ArtifactConfig

Independently versioned release unit within a component.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `ArtifactKey` | yes | Stable artifact identifier unique within the component. |
| `displayName` | `String` | no | Human-readable artifact name. |
| `source` | `SourceKey` | yes | Source key for docs, tags, and refs. |
| `docsRoot` | `RepoRelativePath` | no | Artifact-specific docs root. |
| `assetsRoot` | `RepoRelativePath` | no | Artifact-specific assets root. |
| `versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | yes | Artifact version and ref discovery rules. |
| `publicationSelection` | [PublicationSelectionPolicy](#publicationselectionpolicy) | no | Artifact-level version-context selection policy used during planning and staging. |
| `lifecycle` | [ArtifactLifecycleConfig](#artifactlifecycleconfig) | no | Artifact lifecycle and release-line metadata. |
| `compatibility` | Array<[CompatibilityAssertionConfig](#compatibilityassertionconfig)> | no | Artifact-level compatibility assertions. |
| `mounts` | Array<[MountConfig](#mountconfig)> | no | Artifact-scoped generated or imported documentation mounts. |

<a id="artifactversioningconfig"></a>
## ArtifactVersioningConfig

Artifact-specific version-discovery configuration.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `developmentRef` | `RefString` | yes | Moving mainline ref for development docs. |
| `maintenanceRefPattern` | `String` | no | Pattern used to derive line-head refs, e.g. `releases/{line}`. |
| `tagPattern` | `RegexString` | yes | Regex used to identify artifact release tags. |
| `namedRefs` | Array<[NamedRefConfig](#namedrefconfig)> | no | Intentionally exposed additional named refs such as `preview` or `nightly`. |

<a id="namedrefconfig"></a>
## NamedRefConfig

Authored named ref intentionally exposed as a publishable version context.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `String` | yes | Stable internal identifier such as `preview` or `nightly`. |
| `ref` | `RefString` | yes | SCM ref to materialize for this named context. |
| `displayName` | `String` | no | Human-readable label for selectors or banners. |
| `maturity` | `String` | no | Optional maturity label such as `preview`, `nightly`, or `experimental`. |
| `description` | `String` | no | Optional human-readable explanation of the ref's purpose. |

<a id="publicationselectionpolicy"></a>
## PublicationSelectionPolicy

Separate planning-time policy that determines which version contexts are staged
and surfaced. It is independent from support or maintenance semantics.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `development` | `Boolean` | no | Whether the artifact's development ref is selected. The built-in default is `true`. |
| `lineHeads` | [LineHeadSelectionPolicy](#lineheadselectionpolicy) | no | Which line-head contexts are selected. The built-in default is all authored line heads. |
| `releases` | [ReleaseSelectionPolicy](#releaseselectionpolicy) | no | Which exact releases are selected. The built-in default is the latest stable release per release line. |
| `namedRefs` | `String[]` | no | Explicit authored named-ref keys to expose. The built-in default is none. |
| `candidates` | [CandidateSelectionPolicy](#candidateselectionpolicy) | no | Which release candidates are selected. The built-in default is none. |

<a id="lineheadselectionpolicy"></a>
## LineHeadSelectionPolicy

Selection policy for maintenance or release-line head refs.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `mode` | `LineHeadSelectionMode` | yes | Whether to stage no line heads, all authored line heads, or an explicit subset. |
| `keys` | `String[]` | no | Explicit release-line keys when `mode` is `explicit`. |

<a id="releaseselectionpolicy"></a>
## ReleaseSelectionPolicy

Selection policy for exact released versions.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `mode` | `ReleaseSelectionMode` | yes | How exact releases are selected for staging. |
| `count` | `Integer` | no | Number of releases to keep when `mode` is `latest-n`. |
| `versions` | `VersionString[]` | no | Explicit exact versions when `mode` is `explicit`. |

<a id="candidateselectionpolicy"></a>
## CandidateSelectionPolicy

Selection policy for release candidates.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `mode` | `CandidateSelectionMode` | yes | Whether to stage no candidates, the latest candidate, or an explicit set. |
| `versions` | `VersionString[]` | no | Exact target release versions when `mode` is `explicit`. |
| `externalIds` | `String[]` | no | Optional provider-specific candidate identifiers when a version has multiple candidates and the exact candidate must be pinned. |

<a id="artifactlifecycleconfig"></a>
## ArtifactLifecycleConfig

Artifact-authored lifecycle metadata.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `latestStable` | `VersionString` | no | Latest stable exact release. |
| `releaseLines` | Array<[ReleaseLineConfig](#releaselineconfig)> | no | Artifact release-line definitions. |
| `releases` | Array<[ExactReleaseConfig](#exactreleaseconfig)> | no | Sparse exact-release metadata and publication overrides keyed by version. |
| `supportStatusVocabulary` | `Map<String, [SupportStatusDefinition](#supportstatusdefinition)>` | no | Project-defined support-status vocabulary. |
| `supportPolicyUrl` | `UrlString` | no | Default support-policy URL for the artifact. |
| `defaultSupportWindow` | [SupportWindow](#supportwindow) | no | Default support-window metadata inherited by release lines or releases. |

<a id="exactreleaseconfig"></a>
## ExactReleaseConfig

Authored exact-release metadata or publication override for one version.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `version` | `VersionString` | yes | Exact release version this entry applies to. |
| `releaseLine` | `String` | no | Release-line key when the version is intentionally assigned or overridden. |
| `supportStatus` | `String` | no | Project-defined support-status key for the exact release. |
| `supportWindow` | [SupportWindow](#supportwindow) | no | Structured support-window metadata for the exact release. |
| `publicationState` | `PublicationState` | no | Public visibility and route-preservation state for the release. |
| `withdrawalBehavior` | `WithdrawalBehavior` | no | Behavior to use when `publicationState` is `withdrawn` or `tombstoned`. |
| `redirectTarget` | `String` | no | Internal route reference or fully qualified URL when `withdrawalBehavior` is `redirect`. |
| `reason` | `String` | no | Human-readable explanation for hidden, withdrawn, or tombstoned state. |

<a id="mountconfig"></a>
## MountConfig

Generated or imported documentation subtree mounted into the publication surface.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `source` | `MountSourceRef` | yes | Source path, generated-output reference, or bundle identifier for the mounted subtree. |
| `mountPath` | `PublicPath` | yes | Public path under the owning publication root. |
| `kind` | `String` | yes | Mount type such as `generated-api`, `generated-cli`, or `imported-static-docs`. |
| `versionScope` | `String` | no | Publication scope such as `artifact-release` or `component-root`. |
| `indexBehavior` | `IndexBehavior` | no | Search/index treatment for the mounted subtree. |
| `ownership` | `String` | no | Optional ownership or provenance label. |
| `metadata` | `ExtensionsObject` | no | Optional generator-specific metadata retained for consumers. |

<a id="compatibilityassertionconfig"></a>
## CompatibilityAssertionConfig

Authored compatibility relationship between published identities.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `subjectRef` | `String` | yes | Reference to the subject component, artifact, line, release, or API level. |
| `targetRef` | `String` | yes | Reference to the compatible target component, artifact, line, release, or API level. |
| `relation` | `String` | yes | Relationship such as `compatible-with`, `supports`, `requires`, or `tested-with`. |
| `scope` | `String` | no | Optional granularity such as `release-line`, `exact-release`, or `api-level`. |
| `confidence` | `String` | no | Optional strength such as `declared`, `tested`, or `inferred`. |
| `notes` | `String` | no | Human-facing explanation or caveat. |

<a id="releaselineconfig"></a>
## ReleaseLineConfig

Artifact-authored release-line definition.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `String` | yes | Stable release-line key such as `4.x` or `1.1.x`. |
| `displayName` | `String` | no | Human-readable line label. |
| `parent` | `String` | no | Parent release-line key for hierarchical lines. |
| `latest` | `VersionString` | yes | Latest exact release associated with the line. |
| `supportStatus` | `String` | no | Vocabulary key from the resolved support-status vocabulary. |
| `aliases` | `String[]` | no | Alternate line labels or keys. |
| `maintenanceRef` | `RefString` | no | Explicit line-head ref override for this release line. |
| `supportWindow` | [SupportWindow](#supportwindow) | no | Structured support-window metadata for the line. |

<a id="supportstatusdefinition"></a>
## SupportStatusDefinition

Definition of one support-status vocabulary entry.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `displayName` | `String` | yes | Human-readable label for renderer display. |
| `order` | `Integer` | no | Optional ordering hint for tables or badges. |
| `description` | `String` | no | Optional longer explanation of the status. |
| `defaultMaintenancePhase` | `String` | no | Optional default maintenance-phase hint for this status. |

<a id="supportwindow"></a>
## SupportWindow

Structured support-window metadata for a release line, exact release, or derived version context.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `releaseDate` | `TimestampString` | no | When the release or line became publicly available. |
| `maintenancePhase` | `String` | no | Current or declared phase such as `active`, `maintenance`, `security-fix-only`, or `eol`. |
| `endOfActiveSupportDate` | `TimestampString` | no | End of the active-support period, when distinct. |
| `endOfSupportDate` | `TimestampString` | no | End of support in any form. |
| `endOfLifeDate` | `TimestampString` | no | End-of-life date when distinct from support end. |
| `supportPolicyUrl` | `UrlString` | no | Governing support-policy URL. |
| `notes` | `String` | no | Human-readable notes or caveats. |

<a id="pagetranslationmetadata"></a>
## PageTranslationMetadata

Optional page-authored metadata used to declare translation equivalence across locales.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `translationKey` | `String` | yes | Stable shared key for equivalent pages across locales. The pipeline validates it and copies it into staged front matter and translation aggregates. |

<a id="providersnapshot"></a>
## ProviderSnapshot

Normalized external release-provider input.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `schemaVersion` | `Integer` | yes | Snapshot schema version. |
| `providers` | Array<[ProviderDescriptor](#providerdescriptor)> | yes | Inventory of loaded providers. |
| `records` | Array<[ProviderRecord](#providerrecord)> | yes | Normalized provider records. |

<a id="providerdescriptor"></a>
## ProviderDescriptor

Descriptor for a loaded provider.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `ProviderKey` | yes | Stable provider key used by records. |
| `type` | `String` | yes | Provider implementation type such as `atr` or `github-releases`. |
| `displayName` | `String` | no | Human-readable provider name. |
| `baseUrl` | `UrlString` | no | Provider base URL. |
| `fetchedAt` | `TimestampString` | yes | Timestamp when the provider snapshot was fetched. |

<a id="providerrecord"></a>
## ProviderRecord

Normalized release, candidate, or ref record from a provider.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `provider` | `ProviderKey` | yes | Provider key matching a [ProviderDescriptor](#providerdescriptor). |
| `kind` | `Enum<RecordKind>` | yes | Normalized lifecycle category. |
| `componentSlug` | `Slug` | yes | Target component. |
| `artifactKey` | `ArtifactKey` | yes | Target artifact within the component. |
| `sourceKey` | `SourceKey` | no | Source hint when provider data maps to one source explicitly. |
| `externalId` | `String` | no | Stable provider-owned identifier. |
| `externalUrl` | `UrlString` | no | Human-facing provider URL. |
| `version` | `VersionString` | no | Exact version string. |
| `displayVersion` | `String` | no | Renderer-friendly version label such as `4.1.0-rc2`. |
| `tag` | `String` | no | Exact tag string anchoring the release. |
| `ref` | `RefString` | no | Moving ref such as `main` or `releases/4.x`. |
| `commitSha` | `String` | no | Commit identifier if exposed by the provider. |
| `namedRefKey` | `String` | no | Matching authored named-ref key when the provider enriches a known named ref. |
| `releaseLine` | `String` | no | Release-line key associated with the record. |
| `releaseLineAncestors` | `String[]` | no | Ancestor line keys from narrowest to broadest or project-defined order. |
| `supportStatus` | `String` | no | Project-defined support-status key. |
| `publicationState` | `PublicationState` | no | Provider-observed publication state when a provider can signal withdrawn or hidden releases. |
| `maturity` | `String` | no | Optional maturity label such as `alpha`, `beta`, `rc`, or `preview`. |
| `candidateSequence` | `Integer` | no | Provider-specific candidate number when available. |
| `voteStatus` | `String` | no | Vote or review status for candidate-style records. |
| `createdAt` | `TimestampString` | no | Record creation timestamp. |
| `publishedAt` | `TimestampString` | no | Publication timestamp. |
| `updatedAt` | `TimestampString` | no | Last update timestamp. |
| `urls` | `Map<String, UrlString>` | no | Provider-supplied URLs not promoted to first-class fields. |
| `assets` | Array<[ProviderAsset](#providerasset)> | no | Optional release or candidate assets. |
| `extensions` | `ExtensionsObject` | no | Provider-specific opaque metadata. |

<a id="providerasset"></a>
## ProviderAsset

Optional file-level metadata attached to a provider record.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `name` | `String` | yes | File or asset name. |
| `url` | `UrlString` | yes | Download or detail URL for the asset. |
| `kind` | `String` | no | Advisory asset kind such as `archive`, `signature`, `sbom`, or `package`. |
| `mediaType` | `String` | no | MIME/media type when known. |
| `size` | `Integer` | no | Size in bytes. |
| `checksums` | `Map<String, String>` | no | Checksum map keyed by algorithm, e.g. `sha512`. |
| `signatureUrl` | `UrlString` | no | URL of a detached signature file. |
| `sbomUrl` | `UrlString` | no | URL of an SBOM document. |
| `provenanceUrl` | `UrlString` | no | URL of a provenance or attestation document. |
| `extensions` | `ExtensionsObject` | no | Provider-specific asset metadata. |

<a id="resolvedmaterializationreport"></a>
## ResolvedMaterializationReport

Machine-readable result of a report-only planning command that resolves required
local inputs without fetching or mutating them.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `schemaVersion` | `Integer` | yes | Schema version for the planning report format. |
| `generatedAt` | `TimestampString` | yes | Report generation time. |
| `command` | `String` | yes | Planning intent such as `build` or `watch`. |
| `entries` | Array<[ResolvedMaterializationEntry](#resolvedmaterializationentry)> | yes | Required local inputs and their readiness state. |
| `diagnostics` | Array<[StageDiagnosticEntry](#stagediagnosticentry)> | no | Optional warnings or planning diagnostics. |

<a id="resolvedmaterializationentry"></a>
## ResolvedMaterializationEntry

One required local input discovered by planning.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `sourceKey` | `SourceKey` | no | Source definition that owns the local input when applicable. |
| `componentSlug` | `Slug` | yes | Owning component. |
| `artifactKey` | `ArtifactKey` | no | Owning artifact when the input is artifact-scoped. |
| `kind` | `Enum<RecordKind>` | yes | Lifecycle category of the required input. |
| `releaseLine` | `String` | no | Related release line key when applicable. |
| `version` | `VersionString` | no | Exact released version when applicable. |
| `ref` | `RefString` | no | Related moving ref when applicable. |
| `tag` | `String` | no | Related SCM tag when applicable. |
| `commitSha` | `String` | no | Related exact commit when known. |
| `expectedLocalPath` | `LocalPathString` | yes | Local path expected to contain the staged input tree. |
| `status` | `MaterializationStatus` | yes | Readiness state of the required input. |
| `provenance` | `String` | no | Provenance such as `git-checkout`, `cache-branch`, `snapshot`, or `generated`. |
| `watchEligible` | `Boolean` | no | Whether the input can participate in watch-mode invalidation. |
| `reason` | `String` | no | Optional explanation for missing, stale, or unresolved state. |

<a id="stagemanifest"></a>
## StageManifest

Authoritative entry-point document for a staged output tree.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `schemaVersion` | `Integer` | yes | Schema version for the stage manifest format. |
| `stageLayoutVersion` | `Integer` | yes | Version of the staged-tree layout contract. |
| `generatedAt` | `TimestampString` | yes | Build completion time for the stage root. |
| `command` | `String` | yes | Producing command mode such as `build` or `watch`. |
| `frontMatterFormat` | `String` | yes | Page front matter serialization format, set to `yaml`. |
| `aggregateFormat` | `String` | yes | Aggregate metadata serialization format, set to `json`. |
| `roots` | [StageRoots](#stageroots) | yes | Top-level content, static, and data roots. |
| `dataFiles` | [StageDataFiles](#stagedatafiles) | yes | Aggregate metadata files present in the stage root. |

<a id="stageroots"></a>
## StageRoots

Top-level directory roots within a stage tree.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `content` | `StageRelativePath` | yes | Root directory for staged pages and rendered content inputs. |
| `static` | `StageRelativePath` | yes | Root directory for staged static assets and opaque static mounts. |
| `data` | `StageRelativePath` | yes | Root directory for aggregate metadata files. |

<a id="stagedatafiles"></a>
## StageDataFiles

Inventory of aggregate metadata files present in a stage tree.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `components` | `StageRelativePath` | yes | Path to `data/components.json`. |
| `artifacts` | `StageRelativePath` | yes | Path to `data/artifacts.json`. |
| `routes` | `StageRelativePath` | yes | Path to `data/routes.json`. |
| `redirects` | `StageRelativePath` | yes | Path to `data/redirects.json`. |
| `releases` | `StageRelativePath` | no | Path to `data/releases.json` when release data is present. |
| `candidates` | `StageRelativePath` | no | Path to `data/candidates.json` when candidate data is present. |
| `refs` | `StageRelativePath` | no | Path to `data/refs.json` when named-ref or development data is present. |
| `translations` | `StageRelativePath` | no | Path to `data/translations.json` when translation relationships are present. |
| `compatibility` | `StageRelativePath` | no | Path to `data/compatibility.json` when compatibility assertions are present. |
| `mounts` | `StageRelativePath` | no | Path to `data/mounts.json` when mounted subtrees are present. |
| `providers` | `StageRelativePath` | no | Path to `data/providers.json` when provider snapshots are loaded. |
| `contentIndex` | `StageRelativePath` | no | Path to `data/content-index.json` when content indexing metadata is present. |
| `diagnostics` | `StageRelativePath` | no | Path to `data/diagnostics.json` when non-fatal diagnostics are emitted. |

<a id="stagediagnosticentry"></a>
## StageDiagnosticEntry

Structured warning or informational diagnostic emitted by planning or staging.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `severity` | `DiagnosticSeverity` | yes | Diagnostic severity level. |
| `code` | `String` | yes | Stable diagnostic code. |
| `message` | `String` | yes | Human-readable message. |
| `componentSlug` | `Slug` | no | Related component when applicable. |
| `artifactKey` | `ArtifactKey` | no | Related artifact when applicable. |
| `targetId` | `String` | no | Optional target identifier such as a route, mount, or version-context key. |
| `details` | `ExtensionsObject` | no | Optional structured diagnostic details. |

<a id="sitepipelinecomponentfrontmatter"></a>
## SitePipelineComponentFrontMatter

Pipeline-owned component front matter attached to staged component pages.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `slug` | `Slug` | yes | Stable component identifier. |
| `displayName` | `String` | no | Human-readable component name. |
| `publication` | [ResolvedPublication](#resolvedpublication) | yes | Resolved publication routing and URLs. |
| `artifacts` | Array<[ArtifactFrontMatterSummary](#artifactfrontmattersummary)> | no | Artifact summaries relevant to the component. |

<a id="resolvedpublication"></a>
## ResolvedPublication

Resolved route and URL bundle for a component.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `origin` | [ResolvedOrigin](#resolvedorigin) | yes | Resolved origin information. |
| `paths` | [ResolvedPathSet](#resolvedpathset) | yes | Normalized public paths. |
| `urls` | [ResolvedUrlSet](#resolvedurlset) | yes | Fully qualified URLs derived from the origin and paths. |

<a id="resolvedorigin"></a>
## ResolvedOrigin

Resolved origin information.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `OriginKey` | yes | Origin key from the catalog. |
| `baseUrl` | `UrlString` | yes | Base URL for the origin. |
| `hostname` | `HostnameString` | yes | Hostname extracted from the base URL. |

<a id="resolvedpathset"></a>
## ResolvedPathSet

Resolved public paths.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `component` | `PublicPath` | yes | Component home path. |
| `development` | `PublicPath` | yes | Development content path. |
| `docs` | `PublicPath` | yes | Development docs path. |
| `assets` | `PublicPath` | yes | Development assets path. |

<a id="resolvedurlset"></a>
## ResolvedUrlSet

Resolved fully qualified URLs.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `component` | `UrlString` | yes | Component home URL. |
| `development` | `UrlString` | yes | Development content URL. |
| `docs` | `UrlString` | yes | Development docs URL. |
| `assets` | `UrlString` | yes | Development assets URL. |

<a id="artifactfrontmattersummary"></a>
## ArtifactFrontMatterSummary

Compact artifact summary embedded in component front matter.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `ArtifactKey` | yes | Artifact key. |
| `displayName` | `String` | no | Human-readable artifact name. |
| `latestStable` | `VersionString` | no | Latest stable release. |
| `releaseLines` | Array<[ReleaseLineSummary](#releaselinesummary)> | no | Compact release-line summaries. |

<a id="releaselinesummary"></a>
## ReleaseLineSummary

Compact release-line summary used in front matter or aggregate artifact views.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `String` | yes | Release-line key. |
| `parent` | `String` | no | Parent release-line key. |
| `latest` | `VersionString` | no | Latest exact release in the line. |
| `supportStatus` | `String` | no | Support-status key. |
| `headRef` | `RefString` | no | Resolved or discovered line-head ref. |
| `aliases` | `String[]` | no | Alternate line labels or moving labels associated with the line. |
| `supportWindow` | [SupportWindow](#supportwindow) | no | Structured support-window metadata for the line. |

<a id="sitepipelinecomponentpagefrontmatter"></a>
## SitePipelineComponentPageFrontMatter

Pipeline-owned page-local front matter for staged pages.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `kind` | `String` | yes | Page kind such as `docs-page` or another pipeline-defined page type. |
| `section` | `String` | no | Renderer-oriented page section such as `docs`. |
| `artifactKey` | `ArtifactKey` | no | Artifact associated with the page. |
| `path` | `PublicPath` | yes | Page path under the resolved origin. |
| `url` | `UrlString` | yes | Absolute page URL. |
| `canonicalUrl` | `UrlString` | no | Preferred canonical page URL. |
| `alternateUrls` | `UrlString[]` | no | Alternate equivalent page URLs, typically aliases or locale siblings. |
| `locale` | `String` | no | Locale of the current page. |
| `defaultLocale` | `Boolean` | no | Whether the page belongs to the default locale. |
| `translationKey` | `String` | no | Stable key linking equivalent pages across locales, copied from page-authored translation metadata when present. |
| `translations` | Array<[TranslationLinkSummary](#translationlinksummary)> | no | Available translated siblings for the current page. |
| `componentPath` | `PublicPath` | yes | Component home path for nearby navigation. |
| `componentUrl` | `UrlString` | yes | Component home URL. |
| `version` | [VersionContext](#versioncontext) | no | Version, release, candidate, or ref context for the page. |
| `provider` | [ProviderProvenance](#providerprovenance) | no | Provider provenance for the current page context. |

<a id="versioncontext"></a>
## VersionContext

Version or ref context attached to a staged page.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `kind` | `Enum<RecordKind>` | yes | Lifecycle kind for the page context. |
| `label` | `String` | yes | Human-readable label shown in selectors or banners. |
| `path` | `PublicPath` | no | Version-root path when the page belongs to a published or previewed version root. |
| `url` | `UrlString` | no | Version-root URL. |
| `docsPath` | `PublicPath` | no | Docs-root path for the current version/ref context. |
| `docsUrl` | `UrlString` | no | Docs-root URL for the current version/ref context. |
| `tag` | `String` | no | Release tag when applicable. |
| `ref` | `RefString` | no | Moving ref when applicable. |
| `namedRefKey` | `String` | no | Authored named-ref key when the page belongs to an exposed named ref. |
| `publicationState` | `PublicationState` | no | Publication state of the exact release when applicable. |
| `maturity` | `String` | no | Optional maturity label such as `alpha`, `beta`, `rc`, or `preview`. |
| `candidateSequence` | `Integer` | no | Candidate number when applicable. |
| `voteStatus` | `String` | no | Vote or review status when applicable. |
| `releaseLine` | [ReleaseLineContext](#releaselinecontext) | no | Release-line context for the page. |
| `supportWindow` | [SupportWindow](#supportwindow) | no | Resolved support-window metadata for the current version context. |

<a id="releaselinecontext"></a>
## ReleaseLineContext

Page-local release-line metadata.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `String` | yes | Current release-line key. |
| `supportStatus` | `String` | no | Support-status key for the line. |
| `ancestors` | `String[]` | no | Ancestor release-line keys. |
| `supportWindow` | [SupportWindow](#supportwindow) | no | Structured support-window metadata for the current line. |

<a id="translationlinksummary"></a>
## TranslationLinkSummary

Compact translation sibling reference embedded in front matter.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `locale` | `String` | yes | Locale of the translated sibling. |
| `path` | `PublicPath` | no | Public path of the translated sibling. |
| `url` | `UrlString` | yes | Absolute URL of the translated sibling. |
| `title` | `String` | no | Optional translated title for locale switchers. |

<a id="providerprovenance"></a>
## ProviderProvenance

Compact provider provenance embedded in page front matter.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `ProviderKey` | yes | Provider key. |
| `externalId` | `String` | no | Stable provider-owned identifier for the current context. |
| `externalUrl` | `UrlString` | no | Human-facing provider URL. |

<a id="providersdataentry"></a>
## ProvidersDataEntry

Entry in `data/providers.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `key` | `ProviderKey` | yes | Provider key. |
| `type` | `String` | yes | Provider implementation type. |
| `displayName` | `String` | no | Human-readable provider name. |
| `baseUrl` | `UrlString` | no | Provider base URL. |
| `fetchedAt` | `TimestampString` | yes | Snapshot fetch timestamp. |

<a id="componentsdataentry"></a>
## ComponentsDataEntry

Entry in `data/components.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `slug` | `Slug` | yes | Component identifier. |
| `displayName` | `String` | no | Human-readable component name. |
| `group` | `Identifier` | no | Group key if one applies. |
| `originKey` | `OriginKey` | yes | Resolved publication origin key. |
| `publication` | [ResolvedPublication](#resolvedpublication) | yes | Resolved publication paths and URLs. |
| `providerKeys` | `ProviderKey[]` | no | Providers contributing records for the component. |
| `artifacts` | Array<[ArtifactFrontMatterSummary](#artifactfrontmattersummary)> | no | Component-level artifact summaries. |

<a id="artifactsdataentry"></a>
## ArtifactsDataEntry

Entry in `data/artifacts.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `componentSlug` | `Slug` | yes | Parent component identifier. |
| `key` | `ArtifactKey` | yes | Artifact identifier. |
| `displayName` | `String` | no | Human-readable artifact name. |
| `sourceKey` | `SourceKey` | no | Source backing the artifact. |
| `docsRoot` | `RepoRelativePath` | no | Artifact docs root. |
| `providerKeys` | `ProviderKey[]` | no | Providers contributing data for the artifact. |
| `versioning` | [ArtifactVersioningConfig](#artifactversioningconfig) | no | Artifact versioning configuration summary. |
| `latestStable` | `VersionString` | no | Authored latest stable version if present. |
| `latestRelease` | [LatestReleaseSummary](#latestreleasesummary) | no | Latest exact released version observed or resolved. |
| `latestCandidate` | [LatestCandidateSummary](#latestcandidatesummary) | no | Latest candidate summary. |
| `releaseLines` | Array<[ReleaseLineSummary](#releaselinesummary)> | no | Resolved release-line summaries. |
| `namedRefs` | Array<[RefAggregateEntry](#refaggregateentry)> | no | Intentionally exposed named refs. |
| `supportStatusVocabulary` | `Map<String, [SupportStatusDefinition](#supportstatusdefinition)>` | no | Resolved support-status vocabulary. |
| `supportPolicyUrl` | `UrlString` | no | Resolved support-policy URL for the artifact. |
| `extensions` | `ExtensionsObject` | no | Provider-specific or pipeline-specific extra metadata. |

<a id="latestreleasesummary"></a>
## LatestReleaseSummary

Compact latest-release summary used inside artifact aggregates.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `version` | `VersionString` | yes | Latest exact released version. |
| `displayVersion` | `String` | no | Renderer-friendly label. |
| `tag` | `String` | no | Release tag. |
| `publicationState` | `PublicationState` | no | Publication state of the latest release when it differs from ordinary publication. |
| `publishedAt` | `TimestampString` | no | Publication timestamp. |

<a id="latestcandidatesummary"></a>
## LatestCandidateSummary

Compact latest-candidate summary used inside artifact aggregates.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `version` | `VersionString` | no | Target release version. |
| `displayVersion` | `String` | no | Candidate label such as `4.1.0-rc2`. |
| `candidateSequence` | `Integer` | no | Candidate number. |
| `voteStatus` | `String` | no | Vote or review state. |

<a id="releaseaggregateentry"></a>
## ReleaseAggregateEntry

Entry in `data/releases.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `provider` | `ProviderKey` | no | Provider key when the release came from a provider. |
| `externalId` | `String` | no | Provider-owned identifier. |
| `externalUrl` | `UrlString` | no | Human-facing provider URL. |
| `componentSlug` | `Slug` | yes | Parent component. |
| `artifactKey` | `ArtifactKey` | yes | Parent artifact. |
| `version` | `VersionString` | yes | Exact release version. |
| `displayVersion` | `String` | no | Renderer-friendly version label. |
| `tag` | `String` | no | Release tag. |
| `releaseLine` | `String` | no | Release-line key. |
| `releaseLineAncestors` | `String[]` | no | Ancestor release-line keys. |
| `supportStatus` | `String` | no | Support-status key. |
| `supportWindow` | [SupportWindow](#supportwindow) | no | Structured support-window metadata for the exact release. |
| `publicationState` | `PublicationState` | no | Public visibility and route-preservation state for the exact release. |
| `withdrawalBehavior` | `WithdrawalBehavior` | no | Notice, redirect, or omission policy when the release is withdrawn or tombstoned. |
| `redirectTarget` | `String` | no | Internal route reference or fully qualified URL when `withdrawalBehavior` is `redirect`. |
| `maturity` | `String` | no | Optional maturity label. |
| `publishedAt` | `TimestampString` | no | Publication timestamp. |
| `assets` | Array<[ProviderAsset](#providerasset)> | no | Optional release assets. |
| `urls` | `Map<String, UrlString>` | no | Additional related URLs. |
| `extensions` | `ExtensionsObject` | no | Provider-specific or renderer-specific extra metadata. |

<a id="candidateaggregateentry"></a>
## CandidateAggregateEntry

Entry in `data/candidates.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `provider` | `ProviderKey` | no | Provider key when the candidate came from a provider. |
| `externalId` | `String` | no | Provider-owned identifier. |
| `externalUrl` | `UrlString` | no | Human-facing provider URL. |
| `componentSlug` | `Slug` | yes | Parent component. |
| `artifactKey` | `ArtifactKey` | yes | Parent artifact. |
| `version` | `VersionString` | yes | Target release version. |
| `displayVersion` | `String` | no | Candidate label such as `4.1.0-rc2`. |
| `candidateSequence` | `Integer` | no | Candidate number. |
| `releaseLine` | `String` | no | Release-line key. |
| `maturity` | `String` | no | Optional maturity label, usually `rc` for ASF-style candidates. |
| `voteStatus` | `String` | no | Vote or review status. |
| `createdAt` | `TimestampString` | no | Creation timestamp. |
| `publishedAt` | `TimestampString` | no | Publication timestamp. |
| `assets` | Array<[ProviderAsset](#providerasset)> | no | Optional candidate assets. |
| `extensions` | `ExtensionsObject` | no | Provider-specific or renderer-specific extra metadata. |

<a id="refaggregateentry"></a>
## RefAggregateEntry

Entry in `data/refs.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `provider` | `ProviderKey` | no | Provider key when the ref came from a provider. |
| `externalId` | `String` | no | Provider-owned identifier. |
| `externalUrl` | `UrlString` | no | Human-facing provider URL. |
| `componentSlug` | `Slug` | yes | Parent component. |
| `artifactKey` | `ArtifactKey` | yes | Parent artifact. |
| `kind` | `Enum<development \| named-ref \| line-head>` | yes | Ref category. |
| `namedRefKey` | `String` | no | Authored named-ref key when `kind` is `named-ref`. |
| `ref` | `RefString` | yes | Ref name. |
| `displayVersion` | `String` | no | Friendly label for UI or selector usage. |
| `releaseLine` | `String` | no | Related release-line key when this is a line head. |
| `maturity` | `String` | no | Optional maturity label such as `preview`. |
| `extensions` | `ExtensionsObject` | no | Provider-specific or renderer-specific extra metadata. |

<a id="routeaggregateentry"></a>
## RouteAggregateEntry

Entry in `data/routes.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `originKey` | `OriginKey` | yes | Origin key for the route. |
| `baseUrl` | `UrlString` | yes | Origin base URL. |
| `path` | `PublicPath` | yes | Resolved public path. |
| `url` | `UrlString` | yes | Fully qualified route URL. |
| `componentSlug` | `Slug` | yes | Owning component. |
| `artifactKey` | `ArtifactKey` | no | Related artifact when the route is artifact-specific. |
| `section` | `String` | no | Section such as `component`, `development`, `docs`, or `assets`. |
| `canonical` | `Boolean` | no | Whether the route is canonical for this published target. |
| `routeKind` | `String` | no | Route kind such as `canonical`, `alias`, or `redirect`. |
| `targetId` | `String` | no | Stable identifier for the published target represented by this route. |
| `redirectTargetUrl` | `UrlString` | no | Redirect destination when this route is a redirect. |
| `redirectStatus` | `Integer` | no | Redirect status such as `301`, `302`, `307`, or `308`. |
| `label` | `String` | no | Optional human-facing label such as `latest`. |
| `locale` | `String` | no | Locale associated with the route when locale-aware publication is used. |

<a id="redirectaggregateentry"></a>
## RedirectAggregateEntry

Entry in `data/redirects.json` derived from resolved route metadata.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `fromUrl` | `UrlString` | yes | Fully resolved source URL. |
| `toUrl` | `UrlString` | yes | Fully resolved redirect destination URL. |
| `status` | `Integer` | yes | Redirect status such as `301`, `302`, `307`, or `308`. |
| `reason` | `String` | no | Optional human-facing explanation. |
| `sourceKind` | `String` | no | Why the redirect exists, such as `legacy`, `moving-label`, or `host-migration`. |

<a id="translationsetaggregateentry"></a>
## TranslationSetAggregateEntry

Entry in `data/translations.json` describing one translation set.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `translationKey` | `String` | yes | Stable identifier for equivalent pages across locales, derived from page-authored translation metadata. |
| `componentSlug` | `Slug` | yes | Owning component. |
| `artifactKey` | `ArtifactKey` | no | Related artifact when translation sets are artifact-scoped. |
| `entries` | Array<[TranslationLinkSummary](#translationlinksummary)> | yes | Locale-specific members of the translation set. |

<a id="compatibilityaggregateentry"></a>
## CompatibilityAggregateEntry

Entry in `data/compatibility.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `subjectId` | `String` | yes | Stable identifier for the compatibility subject. |
| `targetId` | `String` | yes | Stable identifier for the compatibility target. |
| `relation` | `String` | yes | Relationship such as `compatible-with`, `supports`, or `requires`. |
| `scope` | `String` | no | Optional relationship granularity. |
| `confidence` | `String` | no | Claim strength such as `declared`, `tested`, or `inferred`. |
| `notes` | `String` | no | Human-facing explanation or caveat. |
| `evidence` | `String[]` | no | Optional supporting references or URLs. |

<a id="mountaggregateentry"></a>
## MountAggregateEntry

Entry in `data/mounts.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `mountId` | `String` | yes | Stable identifier for the mounted subtree. |
| `ownerId` | `String` | yes | Component or artifact owning the mount. |
| `kind` | `String` | yes | Mounted subtree type. |
| `publicPath` | `PublicPath` | yes | Resolved public mount path. |
| `sourceRef` | `MountSourceRef` | yes | Stable source reference for the mounted subtree. |
| `versionContext` | `String` | no | Related release or release-line context. |
| `indexBehavior` | `IndexBehavior` | no | Search/index treatment for the mounted subtree. |
| `metadata` | `ExtensionsObject` | no | Optional generator-specific metadata. |

<a id="contentindexentry"></a>
## ContentIndexEntry

Entry in `data/content-index.json`.

| Field | Type | Req | Description |
| --- | --- | --- | --- |
| `id` | `String` | yes | Stable page identifier within the staged tree. |
| `componentSlug` | `Slug` | yes | Owning component. |
| `artifactKey` | `ArtifactKey` | no | Related artifact when the page is artifact-specific. |
| `pageKind` | `String` | yes | Page kind such as `docs-page` or `component-page`. |
| `section` | `String` | no | Section label for renderer grouping. |
| `originKey` | `OriginKey` | yes | Resolved origin key. |
| `path` | `PublicPath` | yes | Public path of the page. |
| `url` | `UrlString` | yes | Absolute page URL. |
| `canonicalUrl` | `UrlString` | no | Canonical URL for the page. |
| `title` | `String` | no | Page title. |
| `linkTitle` | `String` | no | Short title for navigation links. |
| `description` | `String` | no | Page description. |
| `summary` | `String` | no | Short summary for cards or listings. |
| `weight` | `Integer` | no | Ordering hint. |
| `parentId` | `String` | no | Parent page identifier. |
| `ancestorIds` | `String[]` | no | Ancestor page identifiers. |
| `sourcePath` | `RepoRelativePath` | no | Source file path within the staged or authored tree. |
| `versionKind` | `Enum<RecordKind>` | no | Lifecycle kind for the page context. |
| `versionLabel` | `String` | no | Human-readable version label. |
| `releaseLine` | `String` | no | Release-line key. |
| `supportStatus` | `String` | no | Support-status key. |
| `publicationState` | `PublicationState` | no | Publication state of the exact release when the page belongs to one. |
| `locale` | `String` | no | Locale of the indexed page. |
| `defaultLocale` | `Boolean` | no | Whether the page belongs to the default locale. |
| `translationKey` | `String` | no | Shared translation-set key for equivalent pages. |
| `provider` | `ProviderKey` | no | Provider key for provider-backed page contexts. |
| `externalId` | `String` | no | Provider-owned identifier. |
| `maturity` | `String` | no | Optional maturity label. |
| `candidateSequence` | `Integer` | no | Candidate number when applicable. |
| `voteStatus` | `String` | no | Vote or review status when applicable. |

## Notes on unresolved or intentionally flexible fields

Some fields remain `String` rather than narrower enums because the model does
not try to hard-code semantics that projects or providers may define
differently.

This applies especially to:

- `supportStatus`
- `maintenancePhase`
- `maturity`
- `voteStatus`
- `routeKind`
- page `kind`
- page `section`

That flexibility is intentional. The core model should standardize structural
relationships first, while leaving project- and provider-specific vocabularies
open where needed.