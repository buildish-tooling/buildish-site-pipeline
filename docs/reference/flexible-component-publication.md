---
title: "Flexible component publication model"
description: "This document proposes a more flexible component contract for a green-field Site Pipeline deployment."
weight: 25
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

The central design choice is to separate component identity from public routing:

- `slug` is a stable internal identifier,
- component repositories own content and lifecycle metadata,
- the consumer-owned catalog owns publication layout, and
- the pipeline resolves final publication paths and exposes them to renderers.

## Why change the model

The current contract assumes a shared publication shape centered on
`/components/<slug>/...`.

That is simple, but it couples:

- component identity,
- grouping,
- public URL structure, and
- stage layout assumptions.

If the site needs:

- different groups under different path prefixes,
- some components under custom paths that do not match their group, or
- each component under an explicitly chosen path,

then publication should be modeled explicitly rather than inferred from `slug`.

## Design goals

- let each component publish under an explicit path,
- support multi-host publication, including per-component hostnames,
- support groups as a reusable defaults layer,
- keep component repositories renderer-neutral,
- keep public path design under consumer control,
- expose resolved paths to renderers as authoritative metadata, and
- validate collisions and ambiguous routing strictly.

## Recommended contract split

### Component repository contract

Component-owned metadata should describe only component identity, content roots,
and lifecycle hints.

Preferred structure for `site/component.yaml`:

```yaml
schemaVersion: 1
component:
  slug: spark
  displayName: Apache Spark
content:
  pagesRoot: site/pages
  docsRoot: site/docs
  assetsRoot: site/assets
lifecycle:
  latestStable: v4.0.0
```

The component repository should not own its final public site path.

It should, however, be able to author repository-local content roots safely. In
practice that means a component with `content.docsRoot` can publish a moving
development docs surface even before any consumer models explicit artifacts. If
the consumer resolves that component to `/components/site-pipeline/development/`, the
component-owned `docsRoot` should populate that `/development/` tree without first
inventing an artifact in `site/catalog.yaml`.

### Why the contract is split across two files

New maintainers often expect one authored file to own everything. The pipeline
intentionally does not work that way.

`site/component.yaml` answers "what is true about this repository no matter who
consumes it?" It owns stable component identity, repository-local content roots,
and optional lifecycle hints that remain meaningful across consuming sites.

`site/catalog.yaml` answers "what does this specific site want to publish from
the available repositories and sources?" It owns workspace source bindings,
publication layout, release or ref selection, artifact decomposition, and other
policy that can legitimately differ from one consumer site to another.

That split matters because one repository can be published in more than one way.
One site might publish Apache Spark docs under `/components/spark/`, while
another site might group the same repository under `/analytics/spark/` and only
publish two selected release lines. Neither site should require the repository
itself to rewrite its metadata just to fit one consumer's layout or selection
policy.

The same rule applies to source bindings. A local checkout path, a workspace
overlay, or a consumer-specific source alias is not repository truth. Those are
properties of the current build workspace, so they belong in the consumer
catalog rather than in component-owned metadata.

Artifacts also stay in the consumer catalog on purpose. A component can begin
with only repository-owned `docsRoot` content, which lets one consumer publish a
single development surface immediately. Later, if a consumer needs independent
version selection, release visibility, or publication routing for multiple docs
surfaces, that consumer can model artifacts in `site/catalog.yaml` without
forcing every other consumer of the repository to adopt the same artifact split.

### Consumer catalog contract

The consumer catalog should define both inventory and publication.

This is also where artifact decomposition belongs. That is initially surprising,
but it follows the boundary above: artifacts affect source bindings, publication
selection, release visibility, and final routing, so they are not just
repository facts. They are part of what a specific consumer site chooses to
publish from a repository without letting the repository silently redefine
consumer-owned policy.

Recommended top-level fields in `site/catalog.yaml`:

- `schemaVersion`
- `defaults`
- `site`
- `origins`
- `sources`
- `groups`
- `components`

Recommended `site` section fields:

- `pagesRoot`
- `assetsRoot`
- `vendorAssets`

Recommended `defaults` additions:

- `publication.origin`
- `publication.developmentSegment`
- `publication.docsSegment`
- `publication.assetsSegment`

Recommended `origins` model:

- `baseUrl`
- optional `canonical`
- optional `labels`

Recommended `groups` model:

- `displayName`
- `pathPrefix`
- `navigationSection`
- `weight`
- `publication`

Recommended `sources` model:

- `localDir`
- optional `repository`
- optional `defaultBranch`
- optional `metadataFile`

Recommended per-component additions:

- `weight`
- `group`
- `content.source`
- `publication.origin`
- `publication.pathSegment`
- `publication.mountPath`
- `publication.componentPath`
- `publication.developmentPath`
- `publication.docsPath`
- `publication.assetsPath`
- `artifacts[]`

## Example catalog

```yaml
schemaVersion: 2
defaults:
  metadataFile: site/component.yaml
  pagesRoot: site/pages
  docsRoot: site/docs
  assetsRoot: site/assets
  publication:
    origin: main
    developmentSegment: development
    assetsSegment: assets
site:
  pagesRoot: site/root-pages
  assetsRoot: site/root-assets
  vendorAssets:
    - source: vendor/asf-brand
      mountPath: /assets/vendor/asf-brand/
      kind: vendorStatic
origins:
  main:
    baseUrl: https://www.example.org
  products:
    baseUrl: https://products.example.org
  spark:
    baseUrl: https://spark.example.org
groups:
  libraries:
    displayName: Libraries
    pathPrefix: /libraries/
    navigationSection: Libraries
  platforms:
    displayName: Platforms
    pathPrefix: /platform/
    publication:
      origin: products
components:
  - slug: spark
    localDir: ../spark
    group: libraries
    publication:
      origin: spark
      mountPath: /
  - slug: kafka
    localDir: ../kafka
    group: platforms
    publication:
      mountPath: /streaming/kafka/
  - slug: camel
    localDir: ../camel
    publication:
      mountPath: /integration/
```

In this model:

- `spark` publishes on its own hostname at `https://spark.example.org/`,
- `kafka` inherits the `products` origin from `platforms` and publishes at
  `https://products.example.org/streaming/kafka/`, and
- `camel` publishes on the default hostname at
  `https://www.example.org/integration/`.

## Hostname-aware publication

Once multiple hostnames are allowed, the publication target is no longer just a
path. It becomes a route made of:

- an `origin`, such as `https://www.example.org`, and
- a public path, such as `/libraries/spark/`.

That means the unique publication key is effectively `(origin, path)`.

This model handles several consumer needs cleanly:

- many components on one hostname,
- one hostname per group,
- one hostname per component, and
- the same path reused on different hostnames without collision.

The pipeline should therefore model reusable origins explicitly rather than
copying raw hostnames onto every component.

## Independent release artifacts

Some components do not have one release cadence. They have several independently
versioned deliverables, each with its own tags, support window, and sometimes its
own repository.

That means lifecycle and versioning should not be modeled only at the component
level. The contract needs one more layer:

- a `component` is the user-facing product or documentation space,
- an `artifact` is an independently versioned deliverable within that component,
- a `source` is the repository or checkout from which content and tags are read.

In this model, a component may:

- use one source for shared landing pages,
- use several artifact sources for versioned docs,
- have several `tagPattern` values, one per artifact, and
- mix monorepo and multi-repo release inputs.

Recommended artifact shape:

- `key`
- `displayName`
- `source`
- optional `docsRoot`
- optional `assetsRoot`
- `versioning.developmentRef`
- `versioning.tagPattern`
- optional `versioning.namedRefs[]`
- optional `publicationSelection`
- optional `lifecycle.latestStable`
- optional `lifecycle.releaseLines`
- optional `lifecycle.releases[]`
- optional `lifecycle.supportStatusVocabulary`

Example:

```yaml
sources:
  spark-repo:
    localDir: ../spark
  operator-repo:
    localDir: ../spark-k8s-operator
components:
  - slug: spark
    content:
      source: spark-repo
	artifacts:
		- key: runtime
		  displayName: Spark Runtime
		  source: spark-repo
		  docsRoot: docs/runtime
		  versioning:
			developmentRef: main
			tagPattern: ^v[0-9]+\.[0-9]+\.[0-9]+$
			namedRefs:
				- key: preview
				  ref: preview/docs
				  displayName: Preview
				  maturity: preview
		  publicationSelection:
			namedRefs: [preview]
			releases:
				mode: latestPerLine
		- key: kubernetes-operator
		  displayName: Spark Kubernetes Operator
		  source: operator-repo
		  docsRoot: docs
		  versioning:
			developmentRef: main
			tagPattern: ^operator-v[0-9]+\.[0-9]+\.[0-9]+$
```

With this structure, lifecycle metadata belongs primarily to artifacts. A
component-level lifecycle can also be emitted by the pipeline as a summary, but
it should be treated as derived convenience metadata rather than authored truth.

Publication visibility should stay separate from lifecycle meaning.

That means an artifact may also carry a `publicationSelection` policy used during
planning and staging. When both component and artifact policy are present, the
artifact policy should win.

Effective authored configuration should resolve predictably:

- `defaults` < `group` < `component` < `artifact`
- scalar values use the nearest defined value
- maps merge by key, with the nearer level winning per key
- arrays replace rather than concatenate
- absent values inherit; explicitly empty arrays or maps clear inherited values

To avoid terminology confusion, `artifact` in this document should mean an
independently versioned release unit or documentation stream, not every
downloadable file belonging to a release. Individual tarballs, signatures,
checksums, SBOMs, and attestations should usually hang off release records as
optional asset metadata rather than become top-level pipeline identities.

## Compatibility relationships are first-class metadata

Release identity and support status are not enough for ecosystems such as
Quarkus + Quarkiverse, Camel-family docs, or tool-to-server documentation.

The model should therefore allow explicit compatibility assertions between:

- components,
- artifacts,
- release lines,
- exact releases, or
- named API or protocol levels.

Those relationships should be emitted as aggregate metadata rather than inferred
from matching version strings. That keeps documentation statements such as
"extension line `3.15.x` is compatible with platform line `3.15`" separate from
release identity and separate from support posture.

## Generated and imported documentation mounts

Many projects publish a mix of authored content and generated or imported
reference trees under one version root.

That means the publication model should treat mounted subtrees as a first-class
input, not as an awkward side channel.

Examples include:

- Javadoc or Scaladoc under `/api/java/`
- generated Python reference content under `/api/python/`
- imported OpenAPI or CLI reference bundles

The important distinction is that mounted subtrees share the same publication
system as authored pages without pretending they are identical in provenance or
indexing behavior. They should therefore carry an explicit `trustClass` that
distinguishes passive mounts from imported active browser content.

## Release lines and support phases

Adding release lines such as `1.x` and `1.1.x` does add complexity, but it is the
useful kind of complexity. Without them, renderers can show exact versions, but
they cannot easily build support tables, grouped version selectors, or listings
such as "latest in 1.x" and "latest in 1.1.x".

The clean model is:

- exact releases are immutable versions such as `1.1.7`,
- release lines are named groupings such as `1.x` or `1.1.x`,
- lines belong to artifacts, not components, and
- moving labels such as `stable` or `latest` stay separate from release lines.

Hierarchical lines should be allowed. A release can belong to a narrower line and
that line can point to a broader parent line.

Recommended release line shape:

- `key`
- `displayName`
- optional `parent`
- `latest`
- optional `supportStatus`
- optional `aliases`

Example:

```yaml
artifacts:
  - key: runtime
    displayName: Spark Runtime
    versioning:
      tagPattern: ^v[0-9]+\.[0-9]+\.[0-9]+$
    lifecycle:
      supportStatusVocabulary:
        active:
          displayName: Active
          order: 10
        stable:
          displayName: Stable
          order: 20
        bugfix-only:
          displayName: Bugfix only
          order: 30
        security-fix-only:
          displayName: Security fix only
          order: 40
        eol:
          displayName: End of life
          order: 90
      releaseLines:
        - key: 1.x
          displayName: 1.x
          latest: 1.4.3
          supportStatus: security-fix-only
        - key: 1.1.x
          displayName: 1.1.x
          parent: 1.x
          latest: 1.1.9
          supportStatus: eol
```

### On naming: `status` versus something more specific

I would avoid a generic field name if this is meant to express maintenance or
support posture. A better name is something like:

- `supportStatus`, or
- `supportPhase`

I would slightly prefer `supportStatus` because it reads naturally on a release
line and is easy for renderers to consume.

The important part is not the exact field name, though. The important part is
that the pipeline should not hardcode a global enum for all projects.

Instead, the contract should allow a project-defined vocabulary. For example:

- a component may define a default `supportStatusVocabulary`,
- an artifact may override or narrow that vocabulary,
- each release line may optionally reference one vocabulary key, and
- if no support status is authored, the line simply has no status.

That gives projects room for values like `active`, `stable`, `lts`,
`bugfix-only`, `security-fix-only`, `community-supported`, or `eol` without
forcing the pipeline to pretend those terms are universal.

The pipeline's job should be to validate references and preserve the vocabulary
metadata, not to impose semantics beyond basic structure.

## Authored named refs and publication selection

Intentional preview-style publications should be authored explicitly.

Recommended `namedRefs[]` fields under `versioning`:

- `key`
- `ref`
- optional `displayName`
- optional `maturity`
- optional `description`

Those authored named refs become the stable identities used by planning,
staging, and aggregate metadata. Provider data may enrich them, but provider
records should not be required to create them.

Publication visibility should be controlled by a separate
`publicationSelection` policy rather than by `supportStatus` or release-line
semantics.

Recommended policy dimensions:

- `development`
- `lineHeads`
- `releases`
- `namedRefs`
- `candidates`

Recommended built-in default:

- include development docs
- include all authored line heads
- include the latest stable release per release line
- include only explicitly selected authored named refs
- exclude release candidates unless explicitly requested

This keeps public visibility intentional without making route and lifecycle
metadata carry planning semantics.

Example:

```yaml
	artifacts:
		- key: runtime
		  versioning:
			developmentRef: main
			tagPattern: ^v[0-9]+\.[0-9]+\.[0-9]+$
			namedRefs:
				- key: preview
				  ref: preview/docs
				  displayName: Preview
				  maturity: preview
		  publicationSelection:
			development: true
			lineHeads:
				mode: allAuthored
			releases:
				mode: latestPerLine
			namedRefs: [preview]
			candidates:
				mode: none
```

### Support windows should be structured, but optional

Some projects need more than a support-status key. They need dates and policy
links that explain how long a line or release remains supported.

That is best modeled as a small structured support-window object attached to
release lines and, when needed, exact releases.

Typical fields include:

- `releaseDate`
- `maintenancePhase`
- `endOfActiveSupportDate`
- `endOfSupportDate`
- `endOfLifeDate`
- `supportPolicyUrl`

This is mostly additive lifecycle metadata. It should enrich the current model,
not replace the support-status vocabulary and not absorb compatibility matrices.

## Exact-release publication state

Exact releases sometimes need publication behavior that differs from their
support posture.

That should be modeled separately through exact-release entries under
`lifecycle.releases[]`.

Recommended fields:

- `version`
- optional `releaseLine`
- optional `supportStatus`
- optional `supportWindow`
- optional `publicationState`
- optional `withdrawalBehavior`
- optional `redirectTarget`
- optional `reason`

Recommended `publicationState` vocabulary:

- `published`
- `hidden`
- `withdrawn`
- `tombstoned`

Recommended `withdrawalBehavior` vocabulary:

- `notice`
- `redirect`
- `omit`

This keeps maintenance meaning and publication behavior separate:

- `supportStatus` says how a release is maintained
- `publicationState` says whether and how it is publicly surfaced

For withdrawn or tombstoned releases, the model should support both:

- a notice or tombstone page at the preserved route, and
- an explicit redirect policy to another route or URL

Example:

```yaml
	artifacts:
		- key: runtime
		  lifecycle:
			releases:
				- version: 4.1.0
				  publicationState: withdrawn
				  withdrawalBehavior: notice
				  reason: Recalled pending security fix.
				- version: 3.2.0
				  publicationState: tombstoned
				  withdrawalBehavior: redirect
				  redirectTarget: /security/runtime/3.2.0/
```

## Routing rules

### Core rules

- `slug` is never used implicitly to derive the public URL.
- groups are optional and are not the source of truth for the final URL.
- the final resolved route is always explicit, even when derived from defaults.
- a route is the combination of resolved `origin` and resolved public path.

### Resolution order

The pipeline should resolve the publication origin in this order:

1. per-component `publication.origin`
2. group `publication.origin`
3. `defaults.publication.origin`
4. validation failure if no origin can be resolved

The pipeline should resolve publication paths in this order:

1. explicit per-component paths: `componentPath`, `developmentPath`, `docsPath`,
   `assetsPath`
2. per-component `mountPath`
3. `group.pathPrefix` plus per-component `publication.pathSegment`
4. validation failure if no component mount can be resolved

### Derived defaults

When only `origin` and `mountPath` are provided, the pipeline should derive:

- `componentPath = mountPath`
- `developmentPath = componentPath + <developmentSegment>/`
- `docsPath = developmentPath` unless an explicit `docsPath` or extra
  `docsSegment` override is configured
- `assetsPath = componentPath + <assetsSegment>/`

It should also derive fully qualified URLs by joining each path to the resolved
origin `baseUrl`.

This keeps the common case simple while also allowing a fully explicit routing
map when needed.

### Canonical routes, aliases, and redirects

The route model should distinguish between:

- the published target,
- the canonical route for that target,
- alias routes that also resolve to the same target, and
- redirect routes that forward to another route or URL.

This matters for:

- moving labels such as `latest` or `stable`
- legacy path preservation after a site reorganization
- host migrations
- canonical URL generation for search and feeds

Redirects should be modeled as pipeline-owned route metadata, not primarily as
page markup conventions in Markdown or AsciiDoc.

The pipeline should therefore emit:

- a complete route inventory, and
- a derived redirect inventory that downstream tools can use to generate Apache
  `httpd`, Nginx, CDN, or other deployment-specific config.

### Locale and translation as route dimensions

Locale should be an optional publication dimension that is orthogonal to
component, artifact, and version context.

The model should support:

- no locale path transform (`none`)
- locale-prefixed paths such as `/fr/docs/` (`prefixAll`)
- default-locale behavior
- translation linkage between equivalent pages
- partial translation coverage when some pages exist in only one locale

Host-based locale publication is a later extension rather than part of the
initial implementation contract.

Renderers should receive locale and translation data directly rather than trying
to infer them from path prefixes alone.

Only one locale routing mode should be active for one effective publication. In
the initial implementation that means either `none` or `prefixAll`.

Translation linkage itself should be page-authored rather than catalog-authored.

Pages that belong to the same translation set should carry a shared
`translationKey` in authored page metadata. The pipeline should validate those
keys, derive locale sibling relationships, and emit `data/translations.json`
from the staged page set.

That keeps translation equivalence close to the pages that actually vary by
locale and avoids a brittle central registry in the catalog model.

## How groups should behave

Groups should be treated as a convenience layer rather than as a hard routing
layer.

They are useful for:

- shared hostnames or origins,
- shared path prefixes,
- shared navigation defaults,
- shared weighting defaults, and
- coarse organization in the catalog.

They should not prevent a component from publishing under an arbitrary path.

## External release providers

Site Pipeline should be able to consume release metadata from external systems,
with Apache Trusted Releases (ATR) as one possible provider rather than a hard
coded special case.

That argues for a provider boundary with three properties:

- the pipeline consumes a versioned, normalized snapshot,
- providers may attach extension data without reshaping the core contract, and
- downstream renderers consume staged metadata rather than querying providers
  directly.

This keeps the architecture flexible enough for ATR, Git hosting release APIs,
package registries, or future foundation-wide tooling without turning the core
pipeline into a provider-specific orchestration engine.

### Integration model

The recommended architecture is:

1. an external sync tool or provider adapter pulls provider data,
2. it writes a normalized, versioned snapshot into a pipeline input location,
3. `build()` loads that snapshot during the resolve-and-plan phase,
4. the pipeline merges provider data with authored metadata,
5. staged front matter and aggregate metadata are written from the merged view,
   and
6. renderers consume the staged outputs only.

In this model, webhooks are useful as triggers for refreshing provider snapshots
or starting builds, but they are not the authoritative source of release state.

That fits cleanly into the broader build architecture: provider data is just
another resolved input during planning, not a special renderer-time dependency.

### Normalized provider snapshot

The provider snapshot should have a small stable core and an explicit extension
area.

Recommended top-level shape:

- `schemaVersion`
- `providers[]`
- `records[]`

Recommended `providers[]` fields:

- `key`
- `type`
- optional `displayName`
- optional public `baseUrl`
- `fetchedAt`

Recommended normalized `records[]` core fields:

- `provider`
- `kind`
  - `development`
  - `namedRef`
  - `lineHead`
  - `candidate`
  - `released`
- `componentSlug`
- `artifactKey`
- optional `sourceKey`
- optional `externalId`
- optional `externalUrl`
- optional `version`
- optional `displayVersion`
- optional `tag`
- optional `ref`
- optional `namedRefKey`
- optional `commitSha`
- optional `releaseLine`
- optional `releaseLineAncestors`
- optional `supportStatus`
- optional `publicationState`
- optional `maturity`
- optional `candidateSequence`
- optional `voteStatus`
- optional `createdAt`
- optional `publishedAt`
- optional `updatedAt`
- optional `urls`
- optional `assets`

### Minimal normalized `records[]` schema

To keep provider integrations predictable without freezing the model too early,
the pipeline should define a small minimum contract for every record.

Required for every record:

- `provider`
- `kind`
- `componentSlug`
- `artifactKey`

Additionally, each record should provide at least one stable locator from this
set:

- `externalId`,
- `version`,
- `tag`, or
- `ref`

Kind-specific expectations should remain simple:

- `released`: should normally provide `version` and usually `tag`
- `candidate`: should normally provide `version`; `candidateSequence` is
  recommended when the provider has one
- `namedRef`: should provide `ref`
- `lineHead`: should provide `releaseLine` and usually `ref`
- `development`: should usually provide `ref`

Recommended normalization rules:

- `kind` should come from the small shared vocabulary above
- `componentSlug` and `artifactKey` should reference known pipeline identities
- `version` and `displayVersion` may differ when the provider exposes a friendly
  label such as `4.1.0-rc2`
- `maturity`, `supportStatus`, and `voteStatus` should be optional metadata, not
  required classification keys
- `namedRefKey` should be present when a provider record enriches an authored
  named ref rather than introducing an ad hoc discovered ref
- provider-specific details outside the normalized contract should stay out of
  the v1 public schema for now

This keeps the snapshot useful for indexing and rendering while also allowing a
provider such as ATR to expose richer state over time.

Example minimum shape:

```yaml
records:
  - provider: atr
    kind: released
    componentSlug: spark
    artifactKey: runtime
    externalId: atr:release:spark-runtime:4.0.0
    version: 4.0.0
    tag: v4.0.0
```

This is intentionally a normalized core rather than an exhaustive universal
release schema. Providers may have richer source data, but renderers and
pipeline logic should rely first on the stable core fields and keep unmatched
detail out of the v1 public contract for now.

Example:

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
    kind: namedRef
    componentSlug: spark
    artifactKey: runtime
    ref: feature/docs-reorg
    displayVersion: docs-reorg preview
    maturity: preview
```

### Merge rules

The merge boundary should be explicit.

Authored catalog and component metadata should remain authoritative for:

- publication routing,
- content roots,
- component and artifact identity,
- local grouping and navigation defaults, and
- project-defined support-status vocabularies.

Provider snapshots should be authoritative for externally observed release state,
such as:

- discovered releases,
- release candidates and vote status,
- state for authored named refs or preview refs,
- timestamps,
- external URLs, and
- downloadable asset inventories.

Consumer-authored metadata should remain authoritative for:

- which named refs are intentionally publishable,
- publication-selection policy,
- exact-release publication behavior such as notice vs redirect, and
- final public route ownership.

The pipeline should not let provider data silently redefine consumer-owned URL
layout or component identity. Conversely, authored metadata should not need to
copy volatile provider state such as candidate numbers or vote windows.

When projects need to correct or enrich provider data locally, that should happen
through an explicit override layer rather than by mutating the normalized
provider snapshot in place.

## How much release-file detail to model

This is where the contract can become messy very quickly.

My recommendation is to stop the core model at the level of:

- component,
- artifact,
- release line,
- named ref,
- release candidate, and
- exact release.

The core model should not make every downloadable file a first-class identity.

Instead, exact releases and candidates may optionally carry a generic `assets[]`
list for commonly useful file-level detail. A minimal generic asset shape could
include:

- `name`
- optional `kind`
- `url`
- optional `mediaType`
- optional `size`
- optional `checksums`
- optional `signatureUrl`
- optional `sbomUrl`
- optional `provenanceUrl`

### Minimal optional `assets[]` schema

`assets[]` should stay intentionally lightweight. It exists to power download
tables and release detail pages, not to model every package-management concept in
the core contract.

Required for every asset entry:

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

`kind` should remain advisory rather than exhaustive. Useful values might be:

- `archive`
- `signature`
- `checksum`
- `sbom`
- `provenance`
- `container-image`
- `package`

For checksums, the normalized model should prefer a simple map keyed by
algorithm, for example:

- `sha512`
- `sha256`

Example:

```yaml
assets:
  - name: spark-4.0.0-src.tgz
    kind: archive
    url: https://downloads.example.org/spark-4.0.0-src.tgz
    mediaType: application/gzip
    size: 123456789
    checksums:
      sha512: abcdef...
    signatureUrl: https://downloads.example.org/spark-4.0.0-src.tgz.asc
    sbomUrl: https://downloads.example.org/spark-4.0.0-src.spdx.json
```

That is enough for download listings and release detail pages without forcing the
pipeline to understand every archive, signature, checksum, attestation, or
registry object as its own top-level domain entity.

If a provider exposes richer package or distribution metadata, the pipeline
should leave it out of the v1 public contract rather than inflate the core
schema prematurely.

## Renderer contract

The pipeline should expose resolved paths to renderers in staged metadata and
front matter.

For multi-host publication, exposing only paths is no longer enough. A renderer
or template often needs:

- the current component's origin,
- the current page path relative to that origin,
- the fully qualified canonical URL,
- the component home URL,
- the docs root URL,
- the assets base URL, and
- enough structure to generate cross-links without recomputing routing rules.

The front matter should therefore expose both route parts and resolved URLs.

Pipeline-owned staged front matter should live under a reserved top-level
`pipeline` namespace. Authored page metadata remains outside that namespace, and
authored pages should fail validation if they attempt to define `pipeline`.

Front matter should also expose artifact context when a page belongs to one
specific release stream.

Recommended component-level front matter shape:

```yaml
pipeline:
  component:
    slug: spark
    displayName: Apache Spark
    publication:
      origin: { key: spark, baseUrl: https://spark.example.org, hostname: spark.example.org }
      paths: { component: /, development: /development/, docs: /development/, assets: /assets/ }
      urls: { component: https://spark.example.org/, development: https://spark.example.org/development/, docs: https://spark.example.org/development/, assets: https://spark.example.org/assets/ }
    artifacts:
      - { key: runtime, displayName: Spark Runtime, latestStable: 4.0.0, releaseLines: [{ key: 4.x, latest: 4.0.0, supportStatus: active }] }
      - { key: kubernetes-operator, displayName: Spark Kubernetes Operator, latestStable: 1.3.0 }
```

Recommended page-level front matter shape:

```yaml
pipeline:
  page:
    kind: docsPage
    section: docs
    artifactKey: runtime
    path: /releases/4.0.0/sql/
    url: https://spark.example.org/releases/4.0.0/sql/
    canonicalUrl: https://spark.example.org/releases/4.0.0/sql/
    locale: en
    defaultLocale: true
    translationKey: runtime-sql-overview
    componentPath: /
    componentUrl: https://spark.example.org/
    version:
      kind: released
      label: 4.0.0
      path: /releases/4.0.0/
      url: https://spark.example.org/releases/4.0.0/
      docsPath: /releases/4.0.0/
      docsUrl: https://spark.example.org/releases/4.0.0/
      publicationState: published
      releaseLine: { key: 4.x, supportStatus: active, ancestors: [], supportWindow: { maintenancePhase: active, endOfSupportDate: 2027-06-30T00:00:00Z } }
    translations: [{ locale: fr, url: https://spark.example.org/fr/releases/4.0.0/sql/ }]
```

### Front matter attribute guidance

The necessary attributes break down into a few categories:

- identity: `slug`, `displayName`
- artifact context: `artifactKey`, `artifacts[]`
- origin selection: `origin.key`, `origin.baseUrl`, `origin.hostname`
- public paths: `component`, `development`, `docs`, `assets`
- full URLs: `component`, `development`, `docs`, `assets`
- current page route: page `path` and page `url`
- route semantics: `canonicalUrl`, optional aliases, and redirect-aware routing
- locale and translation context: `locale`, default-locale state, and translated
  siblings derived from page-authored `translationKey`
- version context: development or released version label and URLs
- release-line context: current line, ancestor lines, optional support status,
  and optional support-window metadata
- release provenance: `provider`, `externalId`, `externalUrl`
- preview and candidate context: `ref`, `namedRefKey`, `maturity`,
  `candidateSequence`, and optional `voteStatus`

For reliability, the pipeline should expose both:

- normalized public paths for renderer-relative logic, and
- absolute URLs for canonical links, feeds, sitemaps, redirects, and cross-host
  navigation.

Renderers should consume those resolved values directly and should not reconstruct
URLs from `slug`, group name, internal stage layout, or hostname conventions.

### Front matter versus aggregate metadata

Front matter is necessary, but it is not sufficient for maximum renderer
freedom.

Front matter is best for page-local context:

- what component and artifact the page belongs to,
- what the current resolved URLs are,
- what version context the page is in, and
- what links are immediately relevant to that page.

For global navigation, listings, landing pages, sitemaps, and cross-component UI,
the pipeline should also emit normalized aggregate metadata files.

Recommended staged metadata outputs:

- `data/components.json` for component identity, summaries, groups, origins, and
  publication roots
- `data/artifacts.json` for artifact-level lifecycle, tag patterns, source refs,
  latest stable versions, release lines, support-status vocabularies, and docs
  roots
- `data/releases.json` for exact release records from authored and provider
  inputs, including publication state for hidden, withdrawn, or tombstoned
  releases
- `data/candidates.json` for in-flight release candidates and vote-related state
- `data/refs.json` for development, maintenance, feature, and preview refs when
  they are intentionally exposed, including authored named ref keys when present
- `data/routes.json` for resolved origin/path/url mappings and canonical route
  inventory
- `data/redirects.json` for resolved redirect inventory derived from route
  metadata
- `data/translations.json` for translation-set relationships and locale-specific
  sibling routes
- `data/compatibility.json` for cross-component, cross-artifact, or cross-line
  compatibility assertions
- `data/mounts.json` for mounted generated or imported documentation subtrees
- `data/providers.json` for loaded provider snapshot provenance and fetch state
- `data/content-index.json` for one normalized entry per staged page
- `data/diagnostics.json` for non-fatal warnings, skipped optional inputs, and
  stale-provider notices when present

Recommended `content-index` entry fields:

- stable page id
- component slug
- optional artifact key
- page kind and section
- origin key
- public path and absolute URL
- title, link title, description, summary
- weight and ordering hints
- parent id or ancestor ids derived from the staged content tree
- source file path within the staged tree
- version context
- release-line and support-status context
- support-window metadata when available
- locale and translation-set context when available
- provider provenance and optional maturity/candidate context

That gives a renderer enough information to build:

- arbitrary sidebars,
- drop-down menus from content structure,
- component and artifact listings,
- release selectors,
- release-candidate or preview listings,
- host-aware navigation, and
- locale switchers,
- compatibility tables,
- generated-reference mount sections, and
- alternate views such as cards, tables, or landing-page groupings.

The important distinction is:

- front matter powers rendering of the current page, and
- aggregate metadata powers global queries and information architecture.

## Validation expectations

If publication becomes explicit, validation should also become explicit.

These are natural `site-pipeline check` failures and should be aggregated in one
validation pass where practical.

The pipeline should reject:

- undefined publication origins,
- non-absolute or non-canonical public paths,
- duplicate `(origin, path)` publication routes,
- duplicate canonical routes for the same published target,
- redirect loops or redirects to unknown internal targets,
- redirect targets with unsupported URL schemes,
- overlapping component mounts within the same origin,
- overlapping generated/imported mounts with conflicting ownership,
- duplicate artifact keys within a component,
- ambiguous artifact-to-route mappings,
- duplicate locale entries within one translation set,
- incompatible locale route-mode and origin configuration,
- duplicate authored named ref keys within one artifact,
- authored pages that define the reserved `pipeline` front matter namespace,
- publication-selection policies that reference unknown release lines, named ref
  keys, or exact versions,
- compatibility assertions that reference unknown subjects or targets,
- conflicting tag patterns within one artifact definition,
- provider records that reference unknown components or artifact keys,
- duplicate provider records for the same `(provider, externalId)` pair,
- unknown support-status keys on release lines,
- withdrawn or tombstoned exact releases that declare `withdrawalBehavior:
  redirect` without a redirect target,
- malformed support-window date ordering,
- cycles or broken references in release-line parent chains,
- path-bearing authored or mounted inputs that escape declared roots after
  normalization and symlink resolution,
- collisions with consumer-authored site content,
- collisions between page, docs, and asset mounts for the same component when
  the result would be ambiguous, and
- any configuration that leaves a component without a resolvable public mount.

Detailed path-safety, XSS-defense, redirect-safety, and mounted-content trust
 rules are defined in [security-and-trust-model.md](../security-and-trust-model/).

## Opinionated recommendation

If the project wants maximum flexibility without legacy constraints, the best
contract is:

1. keep `slug` as identity only,
2. model publication as `origin + path`,
3. support groups as defaults rather than as routing truth, and
4. treat artifacts as the unit of release and lifecycle truth,
5. ingest external release state through normalized provider snapshots, and
6. keep file-level distribution details as optional metadata rather than core
   pipeline identity.

That model scales cleanly from a simple grouped site to a fully custom
information architecture.
