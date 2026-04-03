---
weight: 12
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

# Site Pipeline v2 API and contract boundaries

This document defines the public contract boundaries for the Site Pipeline.

The intended principle is:

> The `site-pipeline` executable is the only supported invocation API for stable
> staging operations, specifically `build` and `watch`; the staged tree and
> aggregate metadata are the supported output API for downstream renderers and
> deployment adapters.

## Why this boundary exists

The architecture depends on a clean separation of responsibilities:

- the pipeline owns staging,
- the renderer owns rendering, and
- the consumer owns renderer-specific local development orchestration.

That split keeps the core pipeline portable, container-friendly, and independent
of Hugo, Node-based renderers, themes, dev-server behavior, or publishing logic.

## Stable invocation API

The stable control-plane API is the `site-pipeline` CLI.

The long-term stable commands are:

- `site-pipeline build`
- `site-pipeline watch`

Those commands are the supported way to:

- trigger one-off staging,
- keep staged outputs fresh during local editing,
- run the pipeline in CI,
- invoke the pipeline from container images, and
- integrate the pipeline into editor tasks or consumer wrapper scripts.

The exact CLI surface can evolve, but changes to `build` and `watch` should be
treated as compatibility-sensitive API changes rather than ordinary refactoring.

## Stable outputs API

The stable data-plane API is the staged output contract.

That means downstream consumers should integrate against:

- the staged content tree,
- page-local front matter produced by the pipeline,
- aggregate metadata files such as routes, lifecycle, releases, and related
  indexes, and
- the documented staged directory layout.

Renderers and deployment adapters should treat those staged outputs as the
integration boundary rather than reading arbitrary component repositories or
calling internal Python code.

## What is not a public API

The Python implementation is internal.

This means the following are not public or stable APIs:

- Python modules, classes, and functions in the package
- internal build graph or staging internals
- implementation-specific provider integration code
- internal filesystem or watch-loop helpers
- any future plugin or hook machinery unless documented separately as public

Consumers should not import Site Pipeline internals and should assume they may
change at any time.

## `preview` is not part of the stable contract

`preview` is a debugging convenience, not a stable architectural commitment.

It may remain useful for:

- Site Pipeline development,
- staging-contract debugging, or
- consumer integration debugging when no real renderer dev server is available.

But it is intentionally not the main development story. It is not guaranteed to:

- behave like the real published site,
- remain feature-compatible over time, or
- continue to exist indefinitely.

Consumers should not build their local development architecture around
`site-pipeline preview`.

## Why there is no stable `serve` command

The Site Pipeline should not define a stable `serve` command.

A real development server depends on renderer-specific behavior such as:

- how templates are compiled,
- how Markdown, AsciiDoc, Mermaid, or shortcodes are rendered,
- how hot reload works,
- how themes and static assets are resolved, and
- how the dev server watches files and reports errors.

Pulling that into `site-pipeline` would blur the intended architecture by making
the pipeline responsible for rendering concerns it does not own.

That is why a first-class `serve` command is intentionally out of scope for the
core pipeline API.

## Recommended local development pattern

The preferred local development model is:

1. run `site-pipeline watch`,
2. run the consumer's real renderer dev server, and
3. let the renderer react to staged output changes.

This gives developers a realistic preview of the eventual site while preserving
the staging/rendering separation.

Consumer-owned wrappers such as `make serve` are fine when they orchestrate that
workflow, but those wrappers should remain consumer-specific rather than turning
into core Site Pipeline API.

## Relationship to distribution

This contract is intentionally friendly to both:

- an installed Python package that exposes the `site-pipeline` executable, and
- a container image whose entrypoint is `site-pipeline`.

In both cases, callers use the same invocation API and receive the same staged
output contract.

## Future integrations and add-ons

Renderer-specific examples, wrapper scripts, or helper tooling may still be
useful later.

But those should be treated as isolated integrations layered on top of the core
contracts, not as reasons to widen the core API boundary.

## Read next

- [architecture-overview.md](architecture-overview.md) for the high-level system
  picture
- [source-resolution-and-materialization.md](source-resolution-and-materialization.md)
  for version selection and materialized content inputs
- [build-architecture.md](build-architecture.md) for the recommended execution
  shape of `build` and `watch`
- [flexible-component-publication.md](flexible-component-publication.md) for the
  publication and lifecycle model