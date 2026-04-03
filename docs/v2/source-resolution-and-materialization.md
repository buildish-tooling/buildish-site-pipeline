---
weight: 14
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

# Source resolution and materialization

This document separates three concerns that are easy to mix together when
discussing versioned documentation:

1. **version selection**: which documentation contexts should exist
2. **source materialization**: how those contexts become local input trees
3. **staging**: how local input trees are copied and normalized into the staged
   output contract

```mermaid
flowchart LR
    A[publication model] --> B[version selection]
    B --> C[source materialization]
    C --> D[local content trees]
    D --> E[site-pipeline build/watch]
    E --> F[staged tree and aggregate metadata]
```

## Refs, tags, and line heads are valid source identities

The model supports the core versioned-docs identities:

- development docs may come from a moving development ref
- release-line docs may come from maintenance refs or line heads
- exact release docs may come from immutable tags

That is already reflected in the publication model and schema through concepts
such as `source`, `developmentRef`, `maintenanceRefPattern`, `tagPattern`, and
release-line metadata.

## Consumers should integrate against materialized inputs, not Git itself

The core build contract should not require downstream consumers to think in
terms of raw `git clone` mechanics.

Instead, the important boundary is that `build` and `watch` consume **resolved
local content inputs**.

Those local inputs may come from several strategies, for example:

- direct branch or tag checkouts
- shallow clones or sparse checkouts
- a cache branch such as `versioned-docs`
- immutable exported snapshots or tarballs
- generated local worktrees assembled by consumer-specific tooling

Git is an important implementation strategy, but it should not be the only shape
the architecture can describe.

## A `versioned-docs` branch is a cache strategy, not a publication concept

For projects with very large release histories, re-materializing every
historical tag on every build does not scale well.

A `versioned-docs` branch is a valid optimization for that problem.

Architecturally, it should be treated as:

- a cache or materialization strategy,
- optional,
- replaceable by other strategies later, and
- independent from publication identity and URL structure.

It should **not** be treated as:

- the source of truth for release identity,
- a required lifecycle concept in the publication model, or
- something renderers need to know about.

The publication model talks about development refs, release lines, and
exact releases. A cache branch is simply one way to materialize the content for
those identities efficiently.

## Recommended architectural split

The clean split is:

1. the **publication model** declares what kinds of versioned documentation exist
2. a **selection step** decides which of those contexts are in scope for a build
3. a **materializer** obtains local trees for the selected contexts
4. `site-pipeline build/watch` stages those local trees without owning the SCM
   strategy

This keeps version/lifecycle modeling separate from Git-specific optimization.

## How a consumer should know what to materialize

The consumer should not need to guess from repository state alone.

Instead, there should be a planning step that resolves a desired build scope,
for example:

- current development docs
- one or more maintenance-line heads
- exact releases selected by policy
- explicit preview refs when a site exposes them

That planning step should be driven by the resolved `publicationSelection`
policy for each artifact.

Policy resolution should be:

1. artifact `publicationSelection`, if present
2. component default `publicationSelection`, if present
3. built-in default selection behavior

The built-in default should be:

- include development docs
- include all authored line heads
- include the latest stable release per release line
- include only explicitly selected authored named refs
- exclude release candidates unless explicitly requested

The planning step therefore depends on:

- authored component and artifact config
- release-line metadata
- authored exact-release publication state
- provider snapshots

Provider snapshots may enrich discovered versions and ref state, but they should
not replace the authored selection policy that defines what the site intends to
publish.

The result should be a resolved list of local inputs to stage.

In practical terms, that planning step is a report-only CLI interaction such as
`site-pipeline report-missing` or similar. Its job is to say which version
contexts are required, which local inputs are already present, and which pieces
are missing or stale. It does not itself perform network fetches or cache
mutation.

## Recommended interaction model

The clean interaction model is that the consumer implementation asks
`site-pipeline` what is needed, then uses SCM and cache-specific machinery to
materialize any missing inputs before invoking `build` or `watch`.

```mermaid
sequenceDiagram
    participant Consumer as consumer implementation
    participant Pipeline as site-pipeline CLI
    participant Cache as materialization cache
    participant SCM as SCM systems

    Consumer->>Pipeline: report missing inputs
    Pipeline-->>Consumer: required contexts + present/missing/stale status
    Consumer->>Cache: inspect cached local trees
    alt missing or stale inputs exist
        Consumer->>SCM: fetch or refresh required sources
        SCM-->>Consumer: source snapshots or ref content
        Consumer->>Cache: update materialized local trees
    end
    Consumer->>Pipeline: build or watch
    Pipeline-->>Consumer: staged tree + aggregate metadata
```

In that model, `site-pipeline` remains responsible for planning and staging,
while the consumer implementation remains responsible for acquisition strategy.
That keeps the core pipeline compatible with direct checkouts, cache branches
such as `versioned-docs`, snapshot stores, or other future materialization
mechanisms without turning `build` into an SCM orchestration command.

## Resolved materialization report

The machine-readable planning result is a JSON `ResolvedMaterializationReport`.
It can be emitted to stdout or written to a caller-selected path.

Recommended entry fields include:

- `sourceKey`
- `componentSlug`
- `artifactKey`
- `kind` such as `development`, `line-head`, `released`, or `named-ref`
- optional `releaseLine`
- optional `version`
- optional `ref`
- optional `tag`
- optional `commitSha`
- `expectedLocalPath`
- `status` such as `present`, `missing`, `stale`, or `unresolved`
- `provenance` such as `git-checkout`, `cache-branch`, `snapshot`, or `generated`
- optional `watchEligible`
- optional `reason`

That report lets the build engine say:

- these are the version contexts to stage,
- here is where each local tree lives, and
- here is how each one was materialized.

## What `build` and `watch` should assume

The stable `build` and `watch` commands should assume that the required local
inputs already exist or are described by a resolved materialization report or an
equivalent in-memory plan.

In particular:

- `build` should stage from local resolved inputs
- `build` should not require a full clone of every historical tag
- `watch` should focus mainly on mutable inputs such as development refs and
  local authored content
- immutable historical release snapshots should usually be treated as cached
  inputs rather than watch targets

This keeps `watch` fast and avoids turning it into a generalized SCM sync loop.

## What stays out of the core pipeline contract

The core pipeline should not hard-code:

- how Git fetches are performed
- whether worktrees, clones, or archives are used
- a special status for a branch literally named `versioned-docs`
- network sync policy for historical snapshots
- renderer-visible behavior based on SCM layout details

Those choices belong in consumer-specific tooling or a future dedicated
materialization helper layer.

## Practical interpretation

For a small site, source materialization may be as simple as reading the current
workspace checkout.

For a large site, it may mean:

- reading development docs from a working branch,
- reading maintenance docs from a few moving refs,
- reading historical release docs from a `versioned-docs` cache branch or other
  immutable snapshot store, and
- handing all of those local paths to `site-pipeline build`.

Both cases fit the same architecture.

## Read next

- [architecture-overview.md](architecture-overview.md) for the top-level system
  model
- [api-contract.md](api-contract.md) for stable invocation and output boundaries
- [staged-output-contract.md](staged-output-contract.md) for the staged-tree
  contract consumed by renderers and deployment adapters
- [build-architecture.md](build-architecture.md) for the build/watch execution
  model
- [flexible-component-publication.md](flexible-component-publication.md) for the
  publication and lifecycle model