---
weight: 36
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

# T-shirt size docs to build

This document sketches what a consumable documentation set could look like for
different consumer size bands.

The point is not to define real user-facing docs. The point is to test whether
the model can be explained simply to the intended audience at each size.

The size bands match [model-fit-cross-check.md](model-fit-cross-check.md).

## What this sketch optimizes for

- fast self-identification: "which kind of site am I?"
- a minimal mental model for each audience
- explicit permission to ignore irrelevant complexity
- a clear path to the next size band if a site grows

## Shared shape across all size bands

Every size-oriented doc set should probably include:

- a short "who this is for" page
- a "smallest working shape" page
- an "ignore this for now" section
- a "read this next when you grow" pointer

## Decision matrix for docs emphasis

In the table below, `✓` means the size-oriented doc set should likely include a
real section or page for the topic. `✗` means it can usually be omitted from the
initial docs for that audience, except perhaps as a one-line out-of-scope note.

| Topic | Tiny | Small | Medium | Large | Very-large |
| --- | --- | --- | --- | --- | --- |
| one-component quick start | ✓ | ✓ | ✓ | ✗ | ✗ |
| shorthand/local single-source setup | ✓ | ✓ | ✗ | ✗ | ✗ |
| simple versioning and redirects | ✗ | ✓ | ✓ | ✓ | ✓ |
| mounts for imported or generated docs | ✗ | ✓ | ✓ | ✓ | ✓ |
| multiple artifacts in one product | ✗ | ✗ | ✓ | ✓ | ✓ |
| publication selection and planning | ✗ | ✗ | ✓ | ✓ | ✓ |
| exact-release publication state | ✗ | ✗ | ✓ | ✓ | ✓ |
| grouped components and shared defaults | ✗ | ✗ | ✗ | ✓ | ✓ |
| compatibility relationships | ✗ | ✗ | ✗ | ✓ | ✓ |
| provider snapshot integration | ✗ | ✗ | ✗ | ✓ | ✓ |
| localization and translation linkage | ✗ | ✗ | ✗ | ✗ | ✓ |
| trust boundaries and operational scaling | ✗ | ✗ | ✗ | ✗ | ✓ |

## Tiny

Audience shape:

- one component
- one primary docs tree
- minimal lifecycle surface

Suggested docs to build:

### Start here: tiny sites

- who this is for
- what the pipeline does in one paragraph

### Minimal config for a tiny site

- one component
- one source and one docs root

### Routes and staged output

- where the staged files end up
- what stable route basics the consumer gets

### Ignore for now

- providers, release lines, compatibility, localization

## Small

Audience shape:

- one main product
- simple version navigation
- maybe one mounted API or reference subtree

Suggested docs to build:

### Start here: small sites

- one product, one main artifact, a few versions
- common examples: product docs + downloads + API docs

### Small-site authoring model

- one component, one artifact
- optional mount for generated or imported reference docs

### Versioning and redirects

- latest, development, archive, or a small release history
- aliases and redirects without changing permalinks

### Ignore for now

- grouped components, provider snapshots, translation linkage

## Medium

Audience shape:

- one product plus tools or subprojects
- multiple visible versions
- generated or imported docs are common

Suggested docs to build:

### Start here: medium sites

- one product family with several doc surfaces
- examples: product docs, operator docs, API docs, archived docs

### Components, artifacts, and shared defaults

- one component with several artifacts, or a few related components
- shared publication defaults across those artifacts

### Planning and materialization

- choose which versions and refs to stage
- separate planning from source fetching/materialization

### Lifecycle and publication behavior

- support status vs publication state
- hidden, withdrawn, and tombstoned releases at a high level

## Large

Audience shape:

- one platform plus many modules, extensions, or sibling projects
- several active release lines
- stronger routing and compatibility needs

Suggested docs to build:

### Start here: large sites

- platform plus ecosystem mental model
- shared origins with multiple publication surfaces

### Grouped components and publication policy

- group-level defaults
- publication selection for releases, line heads, named refs, and candidates

### Compatibility and relationship metadata

- which modules work with which platform versions
- how that data reaches staged aggregates and renderers

### Ignore for now

- only skip locale/provider material if the site truly does not need it

## Very-large

Audience shape:

- many repos or doc sources
- multiple product families
- strong permalink continuity needs
- localization and generated refs may both be in play

Suggested docs to build:

### Start here: very-large sites

- the pipeline as a normalization boundary
- authored policy, provider enrichment, and deployment concerns kept separate

### Multi-family publication architecture

- many components and artifacts under one coherent staged contract
- route ownership and long-lived public URL stability

### Provider, locale, and trust boundaries

- provider snapshots enrich but do not own public policy
- translation linkage, mounted content, and security boundaries

### Operational guidance

- planning, caches, materialization strategies, and large redirect inventories

## Consumability check

If this documentation sketch is working, each audience should be able to answer:

1. is this my size band?
2. what is the smallest model I need?
3. which advanced features can I safely ignore?
4. what should I read next if my site grows?

If those questions are hard to answer, the model may still be sound, but the docs
set is not yet consumable enough.

## Recommended next documentation layer

If these docs were actually built, the most useful minimal set would likely be:

- one landing page that helps consumers choose a size band
- one short page per size band
- one shared reference trail into the core design docs for deeper detail

That would give small consumers a short path in, while still letting large
consumers discover the full model without oversimplifying it.