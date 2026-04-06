---
title: "Design review"
description: "This document reviews the current docs as a design set."
weight: 40
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

The goal is not to restate every schema field. The goal is to answer whether the
current design is coherent and whether the greenfield contract set is now
sufficiently explicit to build against.

## Executive summary

The current design is strong.

The most important decisions look correct:

- the architecture boundary is sound
- the public API boundary is sound
- the input and output models broadly fit the intended build/watch architecture
- the lifecycle model is broad enough for real-world projects

The previously loose areas have now been made explicit:

1. staged output structure and manifest contract
2. planning and materialization reporting
3. authored named refs and publication-selection policy
4. page-authored translation linkage
5. withdrawn and tombstoned exact-release behavior
6. the security and trust posture for mounted content and staged metadata

In short: **the design is coherent, explicit, and sufficiently settled to treat
as a greenfield build contract.**

## Architecture assessment

### What looks sound

The core architecture is sound.

The strongest design choices are:

- `site-pipeline` owns staging rather than rendering
- renderers consume staged content and aggregate metadata rather than internal
  Python APIs
- deployment adapters consume route and redirect metadata rather than content
- provider integration is optional and normalized
- source materialization is separated from staging

That separation is especially important for containerized use, large release
histories, and consumer-specific renderer stacks.

The architecture also scales well by site size. A small site can stay close to a
single-component mental model, while large sites can add origins, release lines,
mounts, translations, and compatibility metadata without changing the core idea.

### What deserves continued attention

The architecture is conceptually sound.

The main follow-through area is operational rather than structural: deployment
profiles and isolation choices for imported active mounted content still need to
be implemented carefully by consumers.

## API model assessment

### What looks sound

The API model is sound.

Treating the `site-pipeline` CLI as the stable invocation API, with `build` and
`watch` as the compatibility-sensitive commands, is the right boundary.

The decision to keep `preview` out of the stable contract and to keep `serve`
out of scope for the core pipeline also looks correct.

That keeps the API:

- renderer-neutral
- container-friendly
- testable in CI
- compatible with consumer-owned wrappers

### What remains intentionally restrained

The API model stays appropriately small.

`plan`, `check`, `build`, and `watch` remain the compatibility-sensitive public
CLI surface, without expanding the boundary into SCM orchestration or renderer-
specific behavior.

## Input model assessment

### What looks sound

The input model is broadly sound.

The most successful choices are:

- `component` vs `artifact`
- `source` as a first-class concept
- publication as `origin + path`
- groups as defaults rather than routing truth
- external provider snapshots as normalized optional input
- mounted generated/imported subtrees as first-class input

This is a flexible model without being locked to one site topology.

### Where the input model could be simplified for consumers

The schema itself is reasonably modular, but the consumer experience could still
be simplified in documentation and possibly in a small amount of shorthand.

The main complexity points for consumers are:

- publication path options: `pathSegment`, `mountPath`, `componentPath`,
  `developmentPath`, `docsPath`, and `assetsPath`
- the need to think about `component`, `artifact`, and `source` at the same time
- the split between authored lifecycle hints and provider-derived lifecycle state

This does not necessarily require schema reduction. It mostly requires making the
"small site" path very explicit.

Good simplification options would be:

- stronger documentation for the minimal catalog shape
- continued support for `localDir` shorthand in small setups
- possibly a future primary-artifact shorthand for one-artifact versioned sites,
  if real consumers feel the full artifact structure is too ceremonial

### What is now explicit in the input model

The previously ambiguous authored-model areas are now handled clearly:

- authored `namedRefs[]` define intentional non-development ref contexts
- `publicationSelection` controls which version contexts are staged and exposed
- exact-release `publicationState` and `withdrawalBehavior` separate maintenance
  meaning from public visibility behavior
- translation linkage is explicitly page-authored through `translationKey`

That leaves the input model with normal future-extension room, but not with any
obvious greenfield design hole.

## Output model assessment

### What looks sound

The output model is one of the strongest parts of the design.

The main split is correct:

- page-local front matter for page rendering and nearby navigation
- aggregate metadata for cross-page, cross-component, and deployment-oriented use

The route and redirect separation is also sound. It gives deployment adapters a
server-neutral input without forcing deployment syntax into the core model.

The aggregate set is directionally good for the intended use cases:

- rendering and navigation
- release selectors and listings
- download and candidate pages
- HTTP server/CDN redirect config generation
- translation and compatibility views
- search/content indexing

### What could be simplified or made more robust

The staged contract is explicit and in good shape.

The main remaining simplification opportunity is consumer ergonomics rather than
output structure. The manifest-plus-aggregate approach is appropriate for the
problem space.

### What remains open

The main output-model extension area is how far to standardize diagnostics and
operator-facing reporting over time.

That is no longer a design gap in the stage contract. It is an optional richness
question that can be layered on later if real consumers need it.

## Do the input and output models fit the build architecture?

Yes, broadly.

The fit is good if the resolve-and-plan phase produces an immutable effective
build specification from:

- consumer catalog
- component metadata
- provider snapshots
- source materialization results

Then the rest maps naturally to the current build architecture:

- component workers stage owned subtrees
- the parent process writes shared aggregates
- watch mode reuses the same engine

The main pressure point is multi-version scale. If a component owns many release
contexts, one worker per component may eventually become too coarse. The
build-architecture doc already acknowledges this and leaves room for later
version-level work units.

So the models fit the architecture, but only if source materialization remains a
separate concern and the effective plan is made explicit.

## Security assessment

### Overall assessment

The current design already has some good security instincts:

- provider data is normalized rather than directly trusted as routing truth
- route collisions and redirect problems are treated as validation failures
- materialization is being pushed away from implicit network activity in `build`

The security story is explicit enough to define a defensible baseline for:

- accidental XSS resistance
- malicious or unsafe mounted content handling
- path-escape prevention
- staged-output data minimization
- resource-exhaustion planning

### Main risk areas

#### Path traversal and workspace escape

Several inputs are path-bearing and will need strict validation:

- `localDir`
- `metadataFile`
- `pagesRoot`, `docsRoot`, `assetsRoot`
- mount sources
- materialization cache paths

The current docs define that those paths stay within declared roots after
normalization and symlink resolution.

#### Imported static HTML/JS mounts are a major trust boundary

Mounted generated docs are not all equally safe.

Generated Markdown that is rendered by the main renderer is one thing. Imported
ready-made HTML/JS/CSS trees are another.

If such trees are published under the same origin as the main site, they may be
able to:

- execute arbitrary JavaScript
- interfere with cookies or local storage
- create same-origin XSS or UI-redress problems
- break global navigation assumptions

The current docs treat those mounts as a trust boundary and call out the need for
origin, path, and deployment-policy decisions.

#### Metadata-driven XSS risk

Many fields are plain `String` in the model:

- labels
- descriptions
- notes
- reasons
- titles
- extension fields

The docs define those values as untrusted text unless explicitly typed
otherwise, and renderers are expected to escape them by default.

#### Redirect abuse

`RedirectRuleConfig.target` is a generic `String`.

That leaves room for open-redirect mistakes, unexpected scheme handling, and
consumer confusion between internal route targets and external destinations.

Validation and policy are the right near-term answer here even if the field
remains a string in the schema.

#### Resource exhaustion and denial of service

Potential DoS inputs include:

- huge provider snapshots
- huge redirect inventories
- huge content indexes
- thousands of historical versions
- pathological regexes in tag patterns
- very broad watch roots
- oversized mount metadata or diagnostic-detail payloads

The design now distinguishes between hard non-overridable security ceilings and
safe operational defaults. Future work should validate and tune the defaults
with real consumer usage rather than leave them implicit.

#### Data leakage through staged metadata

The staged outputs should not accidentally expose:

- raw local filesystem paths
- internal cache layout
- internal-only provider URLs
- other machine-local implementation details

The current docs make the intended bias clear: prefer stable public identifiers
over machine-local details.

### Are we prepared to defend against accidental XSS?

Yes, at the contract level.

The design spells out the core posture:

- metadata strings are plain text unless explicitly declared otherwise
- renderers must HTML-escape metadata by default
- dangerous URL schemes are rejected or filtered where appropriate
- imported active HTML/JS mounts are treated as trusted code, not inert content

### Are we prepared to defend against malicious content and bad-site behavior?

Yes, partially at the pipeline-contract level and more fully when paired with a
careful renderer and deployment implementation.

The routing and collision validation story is already fairly good.

The remaining work is mostly operational tuning, deployment profiles, and
consumer-specific isolation policy. The key open design choice is the local
override surface for safe defaults, not whether the public contract should
expose those knobs.

## Recommended security hardening directions

The design should continue to make room for the following:

1. explicit path and symlink safety policy
2. explicit URL-scheme validation policy
3. explicit metadata escaping policy
4. explicit mount trust classes, especially for imported HTML/JS trees
5. keep hard security ceilings small and explicit, while treating large-scale
   count thresholds as safe defaults that can later be tuned locally
6. safe handling of archive extraction and imported bundles
7. continued preference for stable IDs over raw local paths in public outputs

## Lifecycle-model assessment

The lifecycle model is now broad enough for the intended problem space.

It cleanly covers:

- development refs
- line heads
- authored named refs
- exact releases
- release candidates
- support vocabulary and support windows
- publication visibility for hidden, withdrawn, and tombstoned releases

That is a strong result because it keeps support meaning, provider observations,
and publication behavior as separate concerns instead of collapsing them into one
overloaded status field.

## Prioritized recommendations

### Near-term

1. keep examples and future implementation work aligned with the explicit
   publication-selection and exact-release publication-state model
2. preserve the separation between authored policy, provider enrichment, and
   staged outputs during implementation
3. continue treating translation linkage as page-authored metadata rather than
   moving it into a central catalog registry

### Important next

4. refine diagnostics detail only when real consumers need more than the current
   manifest-plus-diagnostics contract
5. define practical operational limits for snapshots, redirects, mounts, and
   content indexes

### Later but likely valuable

6. consider a small-site shorthand if real consumers find the artifact model too
   verbose

## Final verdict

The current docs describe a strong design.

The architecture is sound. The API boundary is sound. The input and output models
are broad enough for the intended problem space and mostly fit the recommended
build architecture.

The main remaining work is not design correction. It is disciplined
implementation, example coverage, and operational hardening.

That is a good place to be. It means the greenfield design appears fundamentally
viable, with the remaining work concentrated in execution rather than in core
architectural correction.
