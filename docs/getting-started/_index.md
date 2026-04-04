---
title: Site Pipeline Getting Started
weight: 10
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

This section helps consumers choose the right entry point for the Site Pipeline
documentation set.

Use the size band that matches your publication shape today. Each page gives a
smallest useful mental model, points out what you can ignore for now, and links
to the next band when your site grows.

## Decision matrix

| Size band | Good fit if your site looks like this | Start here |
| --- | --- | --- |
| tiny | one component, one main docs tree, minimal lifecycle surface | [tiny.md](tiny.md) |
| small | one main product, a few versions, maybe one mounted API or reference subtree | [small.md](small.md) |
| medium | one product family with multiple doc surfaces, generated or imported docs, and publication planning needs | [medium.md](medium.md) |
| large | one platform plus many modules, extensions, or sibling projects with stronger routing and compatibility needs | [large.md](large.md) |
| very-large | many repos or doc sources, multiple product families, localization, and strong permalink continuity requirements | [very-large.md](very-large.md) |

## Topic emphasis matrix

In the table below, `✓` means the size band usually needs that topic in its
normal reading path. `✗` means the topic can usually stay in the background for
that audience.

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

## If you are not sure where to start

- start with [tiny.md](tiny.md) if you have one component and no serious version
  or publication policy yet
- start with [small.md](small.md) if you already need stable latest/development
  routes or simple redirects
- start with [medium.md](medium.md) if the site already has multiple artifacts,
  imported docs, or a planning/materialization step

## Shared follow-on trails

- [../concepts/](../concepts/) for the plain-language model and concrete example
  thread used across the docs
- [../how-to/](../how-to/) for task-oriented guides
- [../architecture/](../architecture/) for system shape, rationale, and examples
- [../reference/](../reference/) for contracts, schemas, and trust-model details
- [../architecture/model-fit-cross-check.md](../architecture/model-fit-cross-check.md) for the
  rationale behind the size bands