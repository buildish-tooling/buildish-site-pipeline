---
weight: 35
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

# Pipeline model fit cross-check

This document cross-checks the current Site Pipeline publication model against
public documentation and release topologies used by prominent OSS projects.

The goal is not to propose migrations. The goal is to test whether the model
described in [flexible component publication](/docs/reference/flexible-component-publication/),
[provider snapshot schema](/docs/reference/provider-snapshot-schema/), and
[pipeline model schema reference](/docs/reference/pipeline-model-schema-reference/) can, in
theory, represent those sites without forcing projects to change their current
permalinks.

## Method and limits

- this is a theory and architecture fit exercise, not an implementation proof
- the analysis is based on public documentation, version selector, and release
  surface patterns visible on project websites as of 2026-04-03
- the question is whether the current model can represent the observed site
  shapes, not whether the current codebase already implements every part of the
  design yet

## What the size categories mean here

The categories below describe documentation topology complexity more than raw
project popularity.

| Category | Meaning |
| --- | --- |
| very-large | many repos or doc sources, multiple product families, multiple release lines, strong permalink stability needs, often generated refs and localization |
| large | one main platform plus many modules, extensions, or sibling projects, with multiple active release lines |
| medium | one main product plus some tools or subprojects, versioned docs, and some generated reference content |
| small | one main product, simple release/version navigation, limited ecosystem sprawl |
| tiny | one component, one primary source, minimal lifecycle surface, usually latest plus maybe archive |

## Executive summary

The current model fits the tested projects well.

The core design choices already look correct:

- explicit `origin + path` instead of hard-coded route conventions
- `component` vs `artifact`
- `source` as a first-class concept
- lifecycle categories for development refs, line heads, releases, and candidates
- separate page-local front matter and aggregate metadata

Beyond those foundations, the model now explicitly covers the most important
publication and relationship features around the edges:

1. redirects, aliases, and canonical routes
2. locale and translation metadata
3. compatibility relationships across components or artifacts
4. imported/generated documentation subtrees
5. richer support-window metadata

## High-level verdict matrix

| Project | Overall fit | Permalink preservation confidence | Main pressure on the model |
| --- | --- | --- | --- |
| Quarkus + Quarkiverse | strong yes | high | compatibility relationships between platform and extension streams |
| Apache Spark | strong yes | high | generated/imported subtrees under one version root |
| Project Nessie org | very strong yes | high | redirects, aliases, and archived version routing |
| Apache Polaris + tools | strong yes | high | grouped family navigation plus moving-label redirects |
| Kubernetes core docs | strong yes | high | localization, support windows, and generated refs |

## Named project cross-checks

### Quarkus, including Quarkus extensions

#### Observed shape

- Quarkus core publishes latest, historical streams, and a development stream
- public routes include both latest-style and explicit version-style paths
- Quarkiverse publishes a large extension ecosystem with many visible version
  streams per extension such as `dev`, `latest`, `3.15.x`, `2.x`, and `1.x`

#### Fit with the current model

This is a strong fit.

Quarkus core can be represented as one component with one main artifact or a
small number of artifacts. Quarkiverse can be represented as a shared origin and
publication family containing many extension components.

The important result is that the model does not require one global docs shape.
It can support:

- one platform site
- a large extension ecosystem
- mixed latest, development, and version-line navigation

#### What Quarkus validates

The important pressure here is compatibility metadata.

For Quarkiverse, an extension docs line often tracks compatibility with a given
Quarkus stream rather than acting as a completely independent product history.
That relationship is now correctly modeled as an explicit compatibility layer,
not as something inferred from exact version, release line, or support status
alone.

#### Conclusion

Quarkus is a strong proof that the `component`, `artifact`, `origin`, `path`,
lifecycle, and compatibility model is directionally correct.

### Apache Spark with subprojects

#### Observed shape

- Spark publishes docs under routes such as `docs/latest/` and exact version
  roots like `docs/4.1.1/`
- subprojects such as SQL, MLlib, GraphX, PySpark, and Structured Streaming are
  presented as sections within one overall documentation publication
- generated reference systems live under the same versioned publication surface

#### Fit with the current model

This is also a strong fit.

Spark is a useful counterexample to a too-granular design. The model does not
force every sub-area into a separate artifact. Spark can still be modeled as one
main component with one primary release train, while major subprojects remain
sections or mounted subtrees within the same published product surface.

#### What Spark validates

Spark strongly validates imported/generated documentation mounts.

Spark mixes authored docs with generated references from different tools. The
model needs a way to say:

- this subtree is authored content
- this subtree is imported or generated content
- both share the same public version root

#### Conclusion

Spark strongly validates the current routing, lifecycle, and mount model.

### Projects in the `projectnessie` GitHub organization

#### Observed shape

- the `nessie` repo acts as the main product center
- the site combines guides, docs, downloads, blog content, release notes, and
  unreleased documentation
- Nessie publicly documents a site reorganization that preserved older links via
  redirects

#### Fit with the current model

This is a very strong fit.

Nessie maps naturally to:

- one main component
- multiple sources if needed
- development docs, exact released docs, archived docs, and tool docs
- aggregate metadata for version navigation and downloads

#### What Nessie validates

The strongest pressure here is redirect and alias handling.

If the architecture goal is to avoid forcing permalink changes, redirects and
aliases need to be treated as publication outputs, not as an implementation
detail outside the model.

#### Conclusion

Nessie is one of the best proofs that the model can handle a real-world
versioned site while preserving legacy permalinks.

### Apache Polaris and its tools

#### Observed shape

- Polaris publishes unreleased and released documentation streams
- the site includes tool documentation under the same overall publication family
- the overall shape is one product plus related tools and release surfaces

#### Fit with the current model

This is a strong fit.

Polaris is a good example of a project family that is bigger than a single repo
but smaller than a full ecosystem like Quarkus or Camel. The current model can
represent this using grouped components, shared origins, and shared publication
defaults.

#### What Polaris validates

Polaris mostly stresses navigation, grouping, and moving-label redirects rather
than schema weakness. The current `group` concept appears sufficient, especially
when combined with explicit redirect inventory for labels like `latest`.

#### Conclusion

Polaris is a good proof that the model works for medium-to-large product
families without needing to become ecosystem-specific.

### Kubernetes

#### Observed shape

- Kubernetes publishes current and several historical doc versions
- the site includes large reference sections and support-policy information
- multiple locales are published in parallel
- generated or imported references are part of the public docs experience

#### Fit with the current model

This is a qualified yes for `kubernetes.io` core docs.

The current model can already represent:

- versioned documentation roots
- development and release context
- aggregate metadata for supported versions
- large component-level content trees

#### What Kubernetes validates

Kubernetes is the clearest validation of locale-aware publication.

The model now needs to carry:

- locale on pages and routes
- default locale and translated variants
- translation linkage between equivalent pages
- locale-aware content indexing

Kubernetes also reinforces the need for support-window metadata and
generated/imported subtree handling.

#### Conclusion

Kubernetes validates the main routing, lifecycle, locale, and mount ideas.

## Representative projects by size band

### Very-large

#### Kubernetes

- validates versioned docs, large content trees, and lifecycle metadata
- validates locale-aware routing, support-window metadata, and generated-ref mounts

#### Apache Camel

Camel publishes many documentation families on one origin, including Camel core,
components, Camel K, Camel Spring Boot, Camel Quarkus, and others, each with
their own visible version surfaces.

Camel is an excellent stress test for:

- shared origins
- grouped products
- multiple active release lines
- product-family navigation
- compatibility relationships across sibling products

### Large

#### Quarkus + Quarkiverse

- platform docs plus a wide extension ecosystem
- strong evidence for grouped components and shared publication defaults

#### Micronaut

Micronaut publishes core docs plus a large module ecosystem under one broad docs
surface with many visible versions. It is another strong validation of the
component/artifact/group model.

#### Istio

Istio mixes latest routes, versioned routes, support windows, release policy,
and localized docs. It reinforces the same model dimensions as Kubernetes,
especially locale-aware publication and structured support metadata.

### Medium

#### Apache Spark

- good fit for one component with large internal sub-areas
- strong requirement for imported/generated documentation mounts

#### Project Nessie

- strong fit for versioned docs plus archived and unreleased docs
- strong requirement for redirects and aliases

#### Apache Polaris

- good fit for one product with related tools and shared publication defaults

#### Keycloak

Keycloak publishes latest docs, nightly docs, archived releases, guides, and API
docs. It is a strong example of a project that mixes authored docs and API docs
without needing a highly customized topology model.

### Small

#### picocli

picocli is a useful small-project sanity check:

- one main manual
- API documentation
- release history and downloads

The important lesson is not complexity. The important lesson is that the model
must collapse gracefully to a very small authored configuration.

#### jsoup

jsoup has a simple but realistic shape: a main site, a cookbook, downloads, and
API docs. This is exactly the kind of project that should be easy to represent
as one component with one primary artifact and one or two mounted reference
subtrees.

### Tiny

#### htmx-style product docs

An htmx-style documentation site is a good proxy for the tiny category:

- one main documentation tree
- one reference section
- a migration guide and some essays or ancillary content

The model should allow this shape with almost no ceremony: one component, one
source, minimal lifecycle metadata, and no provider integration unless the
project explicitly wants it.

## What the current model now covers explicitly

### Redirects, aliases, and canonical routes

The model now treats route semantics as first-class metadata:

- canonical routes
- alias routes such as moving labels like `latest`
- redirect routes
- a derived redirect inventory for deployment-specific config generation

This is the key piece for preserving permalinks across reorganizations and
moving-label policies.

### Locale and translation metadata

Locale is now modeled as an optional publication dimension with:

- locale on pages and routes
- translation linkage between equivalent pages
- locale-aware aggregate metadata
- configurable locale routing policies

### Compatibility relationships

Compatibility is now a separate relationship layer, not something inferred from
release lines or support status. That makes ecosystem cases such as Quarkiverse
or tool-to-server compatibility representable without twisting lifecycle fields.

### Imported and generated documentation mounts

Generated and imported documentation subtrees are now first-class publication
inputs. This allows authored and generated content to share one publication
surface without pretending they have identical provenance.

### Richer support-window metadata

The lifecycle model now has room for structured support-window metadata such as:

- release date
- end-of-active-support date
- end-of-support date
- end-of-life date
- support-policy URL

## What may be overengineered

The core model does not look overengineered. The risk is that the provider and
release layer could become too central.

### Provider snapshots must remain optional

Projects like Quarkus, Spark, Polaris, Nessie, or Kubernetes may benefit from
provider metadata. Small and tiny projects should not need it just to publish a
manual or versioned guide set.

### Candidate and vote metadata should stay additive

Release-candidate, voting, and asset-detail metadata is useful, especially in
ASF-style release processes, but it should remain optional and not shape the
minimal publishing path.

### Deep lifecycle hierarchies should stay optional

Release-line ancestry is useful for some projects, but it should not be assumed
to exist universally.

## Design implications

Based on this cross-check, the current model is suitable for a wide range of
real-world documentation sites.

The remaining work is mostly about:

1. keeping the integrated schema coherent and minimal
2. validating precedence and collision rules across the added dimensions
3. making sure downstream tooling can consume the aggregate metadata cleanly
4. implementing the model incrementally without making provider integration or
   lifecycle detail mandatory for small sites

## Final assessment

The tested projects do not suggest that the core model is fundamentally wrong.
They suggest that it is broad enough to cover the observed site topologies.

The current design is already broad enough to model:

- one-product docs sites
- large extension ecosystems
- grouped project families
- versioned and unreleased docs
- locale-aware publication
- redirect and alias policy
- compatibility relationships
- generated or imported reference mounts
- release and provider metadata

The remaining work is mostly about implementation discipline, validation rules,
and keeping the staged outputs useful for downstream renderers and deployment
adapters.