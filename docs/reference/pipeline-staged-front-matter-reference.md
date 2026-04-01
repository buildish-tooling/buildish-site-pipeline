---
title: "Staged front matter types"
description: "Front matter and page-level metadata emitted into staged content."
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

Front matter and page-level metadata emitted into staged content.

Back to the [reference overview](../pipeline-model-schema-reference/).

## Type index

- [ArtifactFrontMatterSummary](#artifactfrontmattersummary) — Small artifact summary embedded in component front matter.
- [PageSourceProvenance](#pagesourceprovenance) — Repository-neutral pointer to the authored source file for one staged page.
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

<a id="artifactfrontmattersummary"></a>
### ArtifactFrontMatterSummary

Small artifact summary embedded in component front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="artifactfrontmattersummary-key"></a>`key` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | yes | Artifact key used to identify the artifact in page links and typed references. |
| <a id="artifactfrontmattersummary-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable artifact label shown in page chrome or listings. |
| <a id="artifactfrontmattersummary-lateststable"></a>`latestStable` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Most recent stable version that readers should treat as the default recommendation. |
| <a id="artifactfrontmattersummary-releaselines"></a>`releaseLines` | list[[ReleaseLineSummary](#releaselinesummary)] | no | Compact release-line summaries that the page can use for navigation or version selection. |

#### Selected field examples

- `key`: Example: `"runtime"`
- `displayName`: Example: `"Runtime"`
- `latestStable`: Example: `"4.0.1"`

<a id="pagesourceprovenance"></a>
### PageSourceProvenance

Repository-neutral pointer to the authored source file for one staged page.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pagesourceprovenance-key"></a>`key` | [SourceKey](../pipeline-shared-types-reference/#sourcekey) | yes | Resolved source-binding key that owns the authored page. |
| <a id="pagesourceprovenance-path"></a>`path` | [RepoRelativePath](../pipeline-shared-types-reference/#reporelativepath) | yes | Source file path relative to the resolved source binding root. |
| <a id="pagesourceprovenance-repository"></a>`repository` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Remote repository URL whose repository root corresponds to the resolved source binding root, when declared. |
| <a id="pagesourceprovenance-viewref"></a>`viewRef` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Source-control ref that renderers may use for a view-source link. |
| <a id="pagesourceprovenance-editref"></a>`editRef` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Source-control ref that renderers may use for an edit-source link. |

#### Selected field examples

- `key`: Example: `"runtime"`
- `path`: Example: `"docs/getting-started.md"`
- `repository`: Example: `"https://github.com/buildish-tooling/buildish-site-pipeline"`
- `viewRef`: Example: `"main"`
- `editRef`: Example: `"main"`

<a id="pipelinecomponentfrontmatter"></a>
### PipelineComponentFrontMatter

Component-level pipeline metadata injected into staged page front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinecomponentfrontmatter-slug"></a>`slug` | [Slug](../pipeline-shared-types-reference/#slug) | yes | Stable component slug for the owning component. |
| <a id="pipelinecomponentfrontmatter-displayname"></a>`displayName` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Human-readable component name shown in page chrome or navigation. |
| <a id="pipelinecomponentfrontmatter-lateststable"></a>`latestStable` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Most recent stable version recommended for the component as a whole when one shared release line is enough. |
| <a id="pipelinecomponentfrontmatter-publication"></a>`publication` | [ResolvedPublication](#resolvedpublication) | yes | Resolved publication roots and URLs for the owning component. |
| <a id="pipelinecomponentfrontmatter-artifacts"></a>`artifacts` | list[[ArtifactFrontMatterSummary](#artifactfrontmattersummary)] | no | Compact artifact summaries that pages can use for version navigation or page chrome. |

#### Selected field examples

- `slug`: Example: `"spark"`
- `displayName`: Example: `"Apache Spark"`
- `latestStable`: Example: `"4.0.1"`

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
  latestStable: 4.0.0
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
  source:
    key: runtime
    path: docs/getting-started.md
    repository: https://github.com/apache/spark
    viewRef: main
    editRef: main
```

<a id="pipelinepagefrontmatter"></a>
### PipelinePageFrontMatter

Page-local pipeline metadata injected into staged page front matter.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="pipelinepagefrontmatter-kind"></a>`kind` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Short page kind label used by renderers to distinguish landing pages, docs pages, release notes, and similar page families. |
| <a id="pipelinepagefrontmatter-section"></a>`section` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional higher-level section label that groups the page with related navigation or templates. |
| <a id="pipelinepagefrontmatter-artifactkey"></a>`artifactKey` | [ArtifactKey](../pipeline-shared-types-reference/#artifactkey) | no | Artifact key when the page belongs to one independently versioned artifact. |
| <a id="pipelinepagefrontmatter-path"></a>`path` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Published public path for this page. |
| <a id="pipelinepagefrontmatter-url"></a>`url` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Canonical absolute URL for this page. |
| <a id="pipelinepagefrontmatter-canonicalurl"></a>`canonicalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Explicit canonical URL when it should differ from `url`, for example to consolidate duplicate routes. |
| <a id="pipelinepagefrontmatter-alternateurls"></a>`alternateUrls` | list[[UrlString](../pipeline-shared-types-reference/#urlstring)] | no | Additional absolute URLs that should be considered alternate entry points for the same page. |
| <a id="pipelinepagefrontmatter-locale"></a>`locale` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Locale key for this page when it participates in localization. |
| <a id="pipelinepagefrontmatter-defaultlocale"></a>`defaultLocale` | bool | no | Whether this page represents the default locale within its translation group. |
| <a id="pipelinepagefrontmatter-translationkey"></a>`translationKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Shared key that ties translated sibling pages together across locales. |
| <a id="pipelinepagefrontmatter-derivedtitle"></a>`derivedTitle` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Body-derived page title inferred from authored content when the pipeline can detect one. |
| <a id="pipelinepagefrontmatter-deriveddescription"></a>`derivedDescription` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Body-derived page description inferred from authored content when the pipeline can detect one. |
| <a id="pipelinepagefrontmatter-translations"></a>`translations` | list[[TranslationLinkSummary](#translationlinksummary)] | no | Compact links to translated sibling pages in other locales. |
| <a id="pipelinepagefrontmatter-componentpath"></a>`componentPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public root path for the owning component. |
| <a id="pipelinepagefrontmatter-componenturl"></a>`componentUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the owning component root. |
| <a id="pipelinepagefrontmatter-version"></a>`version` | [VersionContext](#versioncontext) | no | Version or ref context attached when this page belongs to a versioned route set. |
| <a id="pipelinepagefrontmatter-provider"></a>`provider` | [ProviderProvenance](#providerprovenance) | no | Pointer back to the upstream provider record that informed the page's version metadata. |
| <a id="pipelinepagefrontmatter-source"></a>`source` | [PageSourceProvenance](#pagesourceprovenance) | no | Repository-neutral provenance for the authored source file that produced this staged page. |

#### Selected field examples

- `kind`: Example: `"docsPage"`
- `section`: Example: `"documentation"`
- `artifactKey`: Example: `"runtime"`
- `path`: Example: `"/spark/4.0.0/docs/getting-started/"`
- `locale`: Example: `"en"`
- `translationKey`: Example: `"spark-overview"`
- `derivedTitle`: Example: `"Getting Started"`
- `derivedDescription`: Example: `"Install the package and run the quickstart."`
- `componentPath`: Example: `"/spark/"`

<a id="providerprovenance"></a>
### ProviderProvenance

Small pointer back to the provider record that informed this page's version.

- category: `emitted`
- ownership: `pipeline-derived`
- file contract: (inner type)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| <a id="providerprovenance-key"></a>`key` | [ProviderKey](../pipeline-shared-types-reference/#providerkey) | yes | Provider key for the upstream system that supplied the current version metadata. |
| <a id="providerprovenance-externalid"></a>`externalId` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Provider-specific stable identifier for the upstream record that informed this page. |
| <a id="providerprovenance-externalurl"></a>`externalUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Human-browsable URL for the upstream record that informed this page. |

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
| <a id="releaselinecontext-key"></a>`key` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Release-line key for this page's version context. |
| <a id="releaselinecontext-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label associated with the current release line. |
| <a id="releaselinecontext-ancestors"></a>`ancestors` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Ancestor release-line keys ordered from nearest to farthest. |
| <a id="releaselinecontext-supportwindow"></a>`supportWindow` | [SupportWindow](../pipeline-authored-input-reference/#supportwindow) | no | Lifecycle dates and support notes attached to the current release line. |

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
| <a id="releaselinesummary-key"></a>`key` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Release-line key, such as `4.0`, for the summarized line. |
| <a id="releaselinesummary-parent"></a>`parent` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Optional parent release-line key when lineage should be preserved in front matter. |
| <a id="releaselinesummary-latest"></a>`latest` | [VersionString](../pipeline-shared-types-reference/#versionstring) | no | Latest released version currently associated with this line. |
| <a id="releaselinesummary-supportstatus"></a>`supportStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Support-status key or label for the release line. |
| <a id="releaselinesummary-headref"></a>`headRef` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Maintenance or line-head ref associated with this release line, if known. |
| <a id="releaselinesummary-aliases"></a>`aliases` | list[[NonEmptyString](../pipeline-shared-types-reference/#nonemptystring)] | no | Alternate labels that should also refer to this release line. |
| <a id="releaselinesummary-supportwindow"></a>`supportWindow` | [SupportWindow](../pipeline-authored-input-reference/#supportwindow) | no | Lifecycle dates and support notes for the release line. |

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
| <a id="resolvedorigin-key"></a>`key` | [OriginKey](../pipeline-shared-types-reference/#originkey) | yes | Origin key selected for this published route or page. |
| <a id="resolvedorigin-baseurl"></a>`baseUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Fully qualified base URL for the selected origin. |
| <a id="resolvedorigin-hostname"></a>`hostname` | [HostnameString](../pipeline-shared-types-reference/#hostnamestring) | yes | Hostname extracted from `baseUrl` for callers that need it without reparsing the URL. |

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
| <a id="resolvedpathset-component"></a>`component` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public root path for the component as a whole. |
| <a id="resolvedpathset-development"></a>`development` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public root path for development-version content. |
| <a id="resolvedpathset-docs"></a>`docs` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public root path for versioned documentation content. |
| <a id="resolvedpathset-assets"></a>`assets` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | yes | Public root path for shared component assets. |

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
| <a id="resolvedurlset-component"></a>`component` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the component root. |
| <a id="resolvedurlset-development"></a>`development` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the development-version root. |
| <a id="resolvedurlset-docs"></a>`docs` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the versioned docs root. |
| <a id="resolvedurlset-assets"></a>`assets` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the shared component asset root. |

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
| <a id="translationlinksummary-locale"></a>`locale` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Locale key for the translated sibling page. |
| <a id="translationlinksummary-path"></a>`path` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Public path for the translated sibling page, if available. |
| <a id="translationlinksummary-url"></a>`url` | [UrlString](../pipeline-shared-types-reference/#urlstring) | yes | Absolute URL for the translated sibling page. |
| <a id="translationlinksummary-title"></a>`title` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Localized page title for the translated sibling page. |

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
| <a id="versioncontext-kind"></a>`kind` | [RecordKind](../pipeline-shared-types-reference/#recordkind) | yes | Kind of version context attached to the page, such as release, candidate, development ref, or named ref. |
| <a id="versioncontext-label"></a>`label` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | yes | Primary label shown to readers for this version context. |
| <a id="versioncontext-path"></a>`path` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Public route root for this version context when it has a routable landing path. |
| <a id="versioncontext-url"></a>`url` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Absolute URL for the version-context route root when it has one. |
| <a id="versioncontext-docspath"></a>`docsPath` | [PublicPath](../pipeline-shared-types-reference/#publicpath) | no | Public docs root for this version context when versioned docs are available. |
| <a id="versioncontext-docsurl"></a>`docsUrl` | [UrlString](../pipeline-shared-types-reference/#urlstring) | no | Absolute URL for the version-context docs root when it has one. |
| <a id="versioncontext-tag"></a>`tag` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Exact tag name associated with this version context, if present. |
| <a id="versioncontext-ref"></a>`ref` | [RefString](../pipeline-shared-types-reference/#refstring) | no | Exact source-control ref associated with this version context, if present. |
| <a id="versioncontext-namedrefkey"></a>`namedRefKey` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Catalog-authored named-ref key when this context represents a named ref. |
| <a id="versioncontext-publicationstate"></a>`publicationState` | [PublicationState](../pipeline-shared-types-reference/#publicationstate) | no | Publication-state label for this version context, such as published or withdrawn. |
| <a id="versioncontext-maturity"></a>`maturity` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Maturity label such as preview, beta, or stable. |
| <a id="versioncontext-candidatesequence"></a>`candidateSequence` | int | no | Release-candidate sequence number when this version context represents a candidate release. |
| <a id="versioncontext-votestatus"></a>`voteStatus` | [NonEmptyString](../pipeline-shared-types-reference/#nonemptystring) | no | Vote status label for release-candidate contexts when it is known. |
| <a id="versioncontext-releaseline"></a>`releaseLine` | [ReleaseLineContext](#releaselinecontext) | no | Release-line context attached to the current version when the version belongs to a known release line. |
| <a id="versioncontext-supportwindow"></a>`supportWindow` | [SupportWindow](../pipeline-authored-input-reference/#supportwindow) | no | Lifecycle dates and support notes attached directly to this version context. |

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

