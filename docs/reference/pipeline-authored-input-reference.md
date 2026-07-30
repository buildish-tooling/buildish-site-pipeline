---
title: "Authored input types"
description: "Consumer-owned and component-owned authored contract models."
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

Consumer-owned and component-owned authored contract models.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Type index

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
- [LinkCheckConfig](#linkcheckconfig) — Site-wide policy for internal page-link validation during ``check``.
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
- [ValidationConfig](#validationconfig) — Optional site-wide validation policies that affect ``check`` behavior.

<a id="artifactconfig"></a>
### ArtifactConfig

One independently versioned release unit inside a component.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactconfig-key"></a>`key` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Stable artifact identifier used in typed references, staged metadata, and provider records. |
| <a id="artifactconfig-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable artifact label shown to readers when the raw key is not ideal UI text. |
| <a id="artifactconfig-source"></a>`source` | [SourceKey](../pipeline-shared-types-reference/#sourcekey) | yes | Named source entry that owns the versioned docs and assets for this artifact. |
| <a id="artifactconfig-docsroot"></a>`docsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Artifact-specific docs root that overrides any inherited docs location when versioned docs live in a custom subdirectory. |
| <a id="artifactconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Artifact-specific asset root that overrides inherited component asset locations for this artifact's versioned output. |
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
| <a id="artifactlifecycleconfig-lateststable"></a>`latestStable` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Most recent stable version that readers should treat as the default recommendation for this artifact. |
| <a id="artifactlifecycleconfig-releaselines"></a>`releaseLines` | list[[ReleaseLineConfig](#releaselineconfig)] | no | Release-line definitions for this artifact, including latest versions and optional support metadata. |
| <a id="artifactlifecycleconfig-releases"></a>`releases` | list[[ExactReleaseConfig](#exactreleaseconfig)] | no | Per-version lifecycle metadata and publication overrides for exact released versions. |
| <a id="artifactlifecycleconfig-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](../pipeline-shared-types-reference/#identifier), [SupportStatusDefinition](#supportstatusdefinition)] | no | Reusable support-status definitions that release lines and exact releases can refer to by key. |
| <a id="artifactlifecycleconfig-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Canonical URL for the support policy document that readers should consult for this artifact. |
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
| <a id="artifactversioningconfig-developmentref"></a>`developmentRef` | [RefString](../pipeline-shared-types-reference/#refstring) | yes | Source-control ref that represents the moving development docs for this artifact. |
| <a id="artifactversioningconfig-maintenancerefpattern"></a>`maintenanceRefPattern` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Pattern used to derive maintenance branch refs from a release-line key, usually with `{line}` as the substitution placeholder. |
| <a id="artifactversioningconfig-tagpattern"></a>`tagPattern` | [RegexString](../pipeline-shared-types-reference/#regexstring) | yes | Regular expression used to recognize provider tags that belong to this artifact's version stream. |
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
| <a id="candidateselectionpolicy-mode"></a>`mode` | [CandidateSelectionMode](../pipeline-shared-types-reference/#candidateselectionmode) | yes | Selection strategy for candidate releases, such as disabling them or selecting an explicit set. |
| <a id="candidateselectionpolicy-versions"></a>`versions` | list[[VersionString](../pipeline-shared-types-reference/#versionstring)] | no | Candidate version strings to include when `mode` is `explicit` and provider versions are available. |
| <a id="candidateselectionpolicy-externalids"></a>`externalIds` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Provider-specific candidate identifiers to include when version strings alone are not enough to identify the desired candidate records. |

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
| <a id="catalogdefaults-metadatafile"></a>`metadataFile` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Default location of `site/component.yaml` within each source tree. |
| <a id="catalogdefaults-pagesroot"></a>`pagesRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Default repository-relative root for non-versioned component pages. |
| <a id="catalogdefaults-docsroot"></a>`docsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Default repository-relative root for component docs content. |
| <a id="catalogdefaults-assetsroot"></a>`assetsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Default repository-relative root for component static assets. |
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
| <a id="compatibilityassertionconfig-subjectref"></a>`subjectRef` | [ReferenceString](../pipeline-shared-types-reference/#referencestring) | yes | Typed internal reference string for the thing whose compatibility is being described. |
| <a id="compatibilityassertionconfig-targetref"></a>`targetRef` | [ReferenceString](../pipeline-shared-types-reference/#referencestring) | yes | Typed internal reference string for the thing that the subject is compatible with or constrained by. |
| <a id="compatibilityassertionconfig-relation"></a>`relation` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Relationship label that names the compatibility statement, such as `testedWith`, `requires`, or `incompatibleWith`. |
| <a id="compatibilityassertionconfig-scope"></a>`scope` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional scope label that narrows the compatibility statement to one subsystem, API surface, or deployment mode. |
| <a id="compatibilityassertionconfig-confidence"></a>`confidence` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional confidence label that tells readers how strong or direct the supporting evidence is. |
| <a id="compatibilityassertionconfig-notes"></a>`notes` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Additional human-readable explanation, caveats, or migration advice for the compatibility statement. |

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
| <a id="componentcatalogentry-slug"></a>`slug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Stable component identifier. |
| <a id="componentcatalogentry-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable component name override or convenience value. |
| <a id="componentcatalogentry-localdir"></a>`localDir` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Simple shorthand for binding the component to one workspace-local checkout directory. |
| <a id="componentcatalogentry-weight"></a>`weight` | int | no | Optional ordering hint for component listings, menus, and other consumer-rendered component collections. |
| <a id="componentcatalogentry-group"></a>`group` | [Identifier](../pipeline-shared-types-reference/#identifier) | no | Optional group key for inherited defaults and renderer grouping. |
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
| <a id="componentcontentselection-source"></a>`source` | [SourceKey](../pipeline-shared-types-reference/#sourcekey) | no | Named source that owns shared component pages, docs, and assets roots. |

<a id="componentidentity"></a>
### ComponentIdentity

Stable identity for a component repository.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentidentity-slug"></a>`slug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Stable component identifier used by consumer catalogs and staged metadata. |
| <a id="componentidentity-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable component name shown in rendered navigation and listings. |

<a id="componentlifecyclehints"></a>
### ComponentLifecycleHints

Optional lifecycle defaults shared across all artifacts in a component repository.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="componentlifecyclehints-lateststable"></a>`latestStable` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Latest stable version for the component when one overall release line is enough. |
| <a id="componentlifecyclehints-supportstatusvocabulary"></a>`supportStatusVocabulary` | dict[[Identifier](../pipeline-shared-types-reference/#identifier), [SupportStatusDefinition](#supportstatusdefinition)] | no | Optional support-status vocabulary shared by artifacts in this repository. |

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
| <a id="contentroots-pagesroot"></a>`pagesRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Repository-relative root for non-versioned component-owned pages. |
| <a id="contentroots-docsroot"></a>`docsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Repository-relative root for versioned or development docs content. |
| <a id="contentroots-assetsroot"></a>`assetsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Repository-relative root for component-owned static assets. |

<a id="exactreleaseconfig"></a>
### ExactReleaseConfig

Per-version lifecycle metadata and publication overrides for one exact release.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="exactreleaseconfig-version"></a>`version` | [VersionString](../pipeline-shared-types-reference/#versionstring) | yes | Exact released version that this metadata entry applies to. |
| <a id="exactreleaseconfig-releaseline"></a>`releaseLine` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Release-line key that this version belongs to when the provider data alone does not already make that relationship obvious. |
| <a id="exactreleaseconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label that should override the line-level status for this exact version. |
| <a id="exactreleaseconfig-supportwindow"></a>`supportWindow` | [SupportWindow](#supportwindow) | no | Lifecycle dates and support notes that apply only to this exact release. |
| <a id="exactreleaseconfig-publicationstate"></a>`publicationState` | [PublicationState](../pipeline-shared-types-reference/#publicationstate) | no | Publication-state override for this version, such as published, withdrawn, or tombstoned. |
| <a id="exactreleaseconfig-withdrawalbehavior"></a>`withdrawalBehavior` | [WithdrawalBehavior](../pipeline-shared-types-reference/#withdrawalbehavior) | no | What readers should experience when this release has been withdrawn, for example a redirect or a hard removal. |
| <a id="exactreleaseconfig-redirecttarget"></a>`redirectTarget` | [ReferenceString](../pipeline-shared-types-reference/#referencestring) \| [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Replacement route or external URL to send readers to when `withdrawalBehavior` is `redirect`. |
| <a id="exactreleaseconfig-reason"></a>`reason` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable explanation of the withdrawal, redirect, or support-state override for this release. |

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
| <a id="groupconfig-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable group name for renderers or generated navigation. |
| <a id="groupconfig-pathprefix"></a>`pathPrefix` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Shared public path prefix applied to grouped component publication roots. |
| <a id="groupconfig-navigationsection"></a>`navigationSection` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional renderer-facing grouping label for navigation or listings. |
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
| <a id="lineheadselectionpolicy-mode"></a>`mode` | [LineHeadSelectionMode](../pipeline-shared-types-reference/#lineheadselectionmode) | yes | Selection strategy for release-line head contexts, such as taking all lines or only an explicit subset. |
| <a id="lineheadselectionpolicy-keys"></a>`keys` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Explicit release-line keys to publish when `mode` is `explicit`. |

#### Selected field examples

- `keys`: Example: `["3.5","4.0"]`

<a id="linkcheckconfig"></a>
### LinkCheckConfig

Site-wide policy for internal page-link validation during `check`.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="linkcheckconfig-enabled"></a>`enabled` | bool | no | Whether the pipeline should validate authored internal page links against resolved public routes. |
| <a id="linkcheckconfig-mode"></a>`mode` | [LinkCheckMode](../pipeline-shared-types-reference/#linkcheckmode) | no | How authored relative page links should resolve in the published site. |
| <a id="linkcheckconfig-checkrootabsolute"></a>`checkRootAbsolute` | bool | no | Whether root-absolute links such as `/components/foo/` should also be validated when they match declared internal prefixes. |
| <a id="linkcheckconfig-internalprefixes"></a>`internalPrefixes` | list[[PublicPath](../pipeline-shared-types-reference/#publicpath)] | no | Root-absolute public-path prefixes that should be treated as internal links when root-absolute checking is enabled. |

#### Selected field examples

- `internalPrefixes`: Example: `["/components/","/docs/"]`

<a id="localizationconfig"></a>
### LocalizationConfig

Locale and translation defaults.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="localizationconfig-defaultlocale"></a>`defaultLocale` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Default locale used when a page does not declare a more specific locale. |
| <a id="localizationconfig-supportedlocales"></a>`supportedLocales` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Supported locale keys for this site or component. |
| <a id="localizationconfig-routemode"></a>`routeMode` | [RouteMode](../pipeline-shared-types-reference/#routemode) | no | How localized pages should be routed within the published URL space. |
| <a id="localizationconfig-fallbacklocale"></a>`fallbackLocale` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Fallback locale used when a requested translation is unavailable. |

<a id="mountconfig"></a>
### MountConfig

Mounted subtree, such as generated API docs or imported assets, published below one public path.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="mountconfig-source"></a>`source` | [MountSourceRef](../pipeline-shared-types-reference/#mountsourceref) | yes | Typed source reference that identifies the generated or imported subtree to mount. |
| <a id="mountconfig-mountpath"></a>`mountPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public path where the mounted subtree should appear in the published site. |
| <a id="mountconfig-kind"></a>`kind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Short kind label that tells renderers and tooling what sort of mounted content this is. |
| <a id="mountconfig-trustclass"></a>`trustClass` | [TrustClass](../pipeline-shared-types-reference/#trustclass) | yes | Trust level for the mounted content, used by downstream tooling to decide how much confidence to place in its structure or metadata. |
| <a id="mountconfig-versionscope"></a>`versionScope` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional label describing which version context this mount belongs to, when the same component can expose several mounted trees. |
| <a id="mountconfig-indexbehavior"></a>`indexBehavior` | [IndexBehavior](../pipeline-shared-types-reference/#indexbehavior) | no | How the mounted subtree should participate in generated indexes, listings, or navigation structures. |
| <a id="mountconfig-ownership"></a>`ownership` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Logical owner label used in staged metadata to explain who is responsible for this mounted subtree. |
| <a id="mountconfig-metadata"></a>`metadata` | [ExtensionsObject](../pipeline-shared-types-reference/#extensionsobject) | no | Small JSON-like extension object for extra mount metadata that downstream tooling may consume. |

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
| <a id="namedrefconfig-key"></a>`key` | [Identifier](../pipeline-shared-types-reference/#identifier) | yes | Stable identifier used elsewhere in the catalog to select this named ref. |
| <a id="namedrefconfig-ref"></a>`ref` | [RefString](../pipeline-shared-types-reference/#refstring) | yes | Exact source-control ref to resolve when this named context is selected. |
| <a id="namedrefconfig-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable label shown in version pickers, breadcrumbs, or other rendered UI. |
| <a id="namedrefconfig-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short maturity label that explains how stable or experimental this named ref should be treated. |
| <a id="namedrefconfig-description"></a>`description` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable explanation of what this named ref contains or who should use it. |

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
| <a id="originconfig-baseurl"></a>`baseUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Base public URL for this publication origin. |
| <a id="originconfig-canonical"></a>`canonical` | bool | no | Whether this origin should be treated as canonical when multiple origins publish the same target. |
| <a id="originconfig-labels"></a>`labels` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Optional human-readable labels for renderer or deployment tooling. |

<a id="publicationconfig"></a>
### PublicationConfig

Resolved-or-authored route layout choices for a component or artifact.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="publicationconfig-origin"></a>`origin` | [OriginKey](../pipeline-shared-types-reference/#originkey) | no | Publication origin key to use for this component or artifact. |
| <a id="publicationconfig-pathsegment"></a>`pathSegment` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Path segment appended below an inherited path prefix or mount root. |
| <a id="publicationconfig-mountpath"></a>`mountPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Explicit public root path for the component's published content. |
| <a id="publicationconfig-componentpath"></a>`componentPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Explicit public path for the component landing page or overview root. |
| <a id="publicationconfig-developmentpath"></a>`developmentPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Explicit public path for the moving development docs surface. |
| <a id="publicationconfig-docspath"></a>`docsPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Explicit public docs landing path exposed to downstream consumers; defaults to the development path unless an additional docs segment or override is configured. |
| <a id="publicationconfig-assetspath"></a>`assetsPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Explicit public path for static assets below the component root. |
| <a id="publicationconfig-canonicalpath"></a>`canonicalPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Optional canonical public path used when aliases or multiple origins are present. |
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
| <a id="publicationselectionpolicy-namedrefs"></a>`namedRefs` | list[[Identifier](../pipeline-shared-types-reference/#identifier)] | no | Named ref keys to include as publishable contexts in addition to development, line-head, or released versions. |
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
| <a id="redirectruleconfig-frompath"></a>`fromPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public path that should redirect instead of serving its own content. |
| <a id="redirectruleconfig-fromorigin"></a>`fromOrigin` | [OriginKey](../pipeline-shared-types-reference/#originkey) | no | Optional origin override when the redirect should only exist on one named publication origin. |
| <a id="redirectruleconfig-target"></a>`target` | [ReferenceString](../pipeline-shared-types-reference/#referencestring) \| [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Destination of the redirect, either as a typed internal reference string or as a fully qualified external URL. |
| <a id="redirectruleconfig-status"></a>`status` | int | no | HTTP redirect status to emit; when omitted, downstream tooling applies its default redirect status. |
| <a id="redirectruleconfig-reason"></a>`reason` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short explanation of why the redirect exists, for example to describe a rename, consolidation, or withdrawn release route. |

#### Selected field examples

- `fromPath`: Example: `"/spark/docs/current/"`
- `fromOrigin`: Example: `"archive"`
- `target`: Example: `"route:/spark/development/"`
- `status`: Example: `308`
- `reason`: Example: `"Development docs moved to the new route."`

<a id="releaselineconfig"></a>
### ReleaseLineConfig

One logical release line, such as `4.0`, together with its lifecycle metadata.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="releaselineconfig-key"></a>`key` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Stable key for the release line, typically matching the family label used in URLs and navigation. |
| <a id="releaselineconfig-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable label shown to readers when the raw line key is not ideal UI text. |
| <a id="releaselineconfig-parent"></a>`parent` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional parent release-line key used to model lineage such as `4.x` inheriting from `3.x` policy or navigation structure. |
| <a id="releaselineconfig-latest"></a>`latest` | [VersionString](../pipeline-shared-types-reference/#versionstring) | yes | Latest released version currently considered the head of this release line. |
| <a id="releaselineconfig-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label that should be shown for the line as a whole. |
| <a id="releaselineconfig-aliases"></a>`aliases` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Alternate labels that should also resolve to this release line in generated metadata or UI. |
| <a id="releaselineconfig-maintenanceref"></a>`maintenanceRef` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Explicit maintenance branch ref for the line when it should not be derived from `maintenanceRefPattern`. |
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
| <a id="releaseselectionpolicy-mode"></a>`mode` | [ReleaseSelectionMode](../pipeline-shared-types-reference/#releaseselectionmode) | yes | Selection strategy for released versions, for example the latest `n` releases or one explicit version list. |
| <a id="releaseselectionpolicy-count"></a>`count` | [PositiveInteger](../pipeline-shared-types-reference/#positiveinteger) | no | How many most-recent releases to include when `mode` is `latestN`. |
| <a id="releaseselectionpolicy-versions"></a>`versions` | list[[VersionString](../pipeline-shared-types-reference/#versionstring)] | no | Exact released versions to include when `mode` is `explicit`. |

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
| <a id="routealiasconfig-path"></a>`path` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Alternate public path that should resolve to the same page family or landing target as the primary route. |
| <a id="routealiasconfig-origin"></a>`origin` | [OriginKey](../pipeline-shared-types-reference/#originkey) | no | Optional origin override when the alias should only exist on one named publication origin. |
| <a id="routealiasconfig-label"></a>`label` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable label that renderers can use when presenting this alias in navigation or metadata. |

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
| <a id="sitecatalogdocumentv1-origins"></a>`origins` | dict[[OriginKey](../pipeline-shared-types-reference/#originkey), [OriginConfig](#originconfig)] | no | Named publication origins that components can target. |
| <a id="sitecatalogdocumentv1-sources"></a>`sources` | dict[[SourceKey](../pipeline-shared-types-reference/#sourcekey), [SourceConfig](#sourceconfig)] | no | Named repository or checkout bindings used by components and artifacts. |
| <a id="sitecatalogdocumentv1-groups"></a>`groups` | dict[[Identifier](../pipeline-shared-types-reference/#identifier), [GroupConfig](#groupconfig)] | no | Optional grouping defaults shared by multiple components. |
| <a id="sitecatalogdocumentv1-validation"></a>`validation` | [ValidationConfig](#validationconfig) | no | Optional site-wide validation policies that extend the default `check` behavior. |
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
| <a id="sitecontentconfig-pagesroot"></a>`pagesRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Repository-relative root for consumer-owned top-level site pages. |
| <a id="sitecontentconfig-assetsroot"></a>`assetsRoot` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Repository-relative root for consumer-owned top-level static assets. |
| <a id="sitecontentconfig-vendorassets"></a>`vendorAssets` | list[TopLevelAssetConfig] | no | Additional imported asset trees mounted into the top-level site assets area. |

<a id="sourceconfig"></a>
### SourceConfig

Named repository or checkout binding reused by components and artifacts.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="sourceconfig-localdir"></a>`localDir` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | yes | Workspace-relative checkout or source directory. |
| <a id="sourceconfig-repository"></a>`repository` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Optional remote repository URL associated with this source. |
| <a id="sourceconfig-defaultbranch"></a>`defaultBranch` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Optional default branch or ref for this source. |
| <a id="sourceconfig-metadatafile"></a>`metadataFile` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | no | Optional override for the component metadata file inside this source tree. |

<a id="supportstatusdefinition"></a>
### SupportStatusDefinition

One reusable support-status label, description, and default lifecycle behavior.

- category: `authored`
- ownership: `component-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="supportstatusdefinition-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Human-readable status label shown to readers, such as `Supported` or `Security fixes only`. |
| <a id="supportstatusdefinition-order"></a>`order` | int | no | Optional sort order used when several support statuses should appear in a stable display order. |
| <a id="supportstatusdefinition-description"></a>`description` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable explanation of what this support status means in practice. |
| <a id="supportstatusdefinition-defaultmaintenancephase"></a>`defaultMaintenancePhase` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Default maintenance-phase label to apply when a release uses this support status and does not provide a more specific phase. |

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
| <a id="supportwindow-releasedate"></a>`releaseDate` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Release date for the line or version that this support window describes. |
| <a id="supportwindow-maintenancephase"></a>`maintenancePhase` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Short label for the current maintenance phase, such as general availability, maintenance, or security-only support. |
| <a id="supportwindow-endofactivesupportdate"></a>`endOfActiveSupportDate` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Date after which the release no longer receives full active support. |
| <a id="supportwindow-endofsupportdate"></a>`endOfSupportDate` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Date after which the release is no longer supported in normal maintenance channels. |
| <a id="supportwindow-endoflifedate"></a>`endOfLifeDate` | [TimestampString](../pipeline-shared-types-reference/#timestampstring) | no | Final retirement date after which the release should be treated as fully end-of-life. |
| <a id="supportwindow-supportpolicyurl"></a>`supportPolicyUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Canonical URL that explains the support policy referenced by this support window. |
| <a id="supportwindow-notes"></a>`notes` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Additional notes that clarify exceptions, migration advice, or support caveats. |

#### Selected field examples

- `releaseDate`: Example: `"2026-04-01T00:00:00Z"`
- `maintenancePhase`: Example: `"security-fixes"`

<a id="validationconfig"></a>
### ValidationConfig

Optional site-wide validation policies that affect `check` behavior.

- category: `authored`
- ownership: `consumer-owned`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="validationconfig-linkchecks"></a>`linkChecks` | [LinkCheckConfig](#linkcheckconfig) | no | Optional internal page-link checking policy resolved against staged public routes. |

