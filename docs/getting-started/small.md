---
title: Small sites
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

This page is for one main product with a small visible release history and maybe
one mounted API, generated reference tree, or imported docs subtree.

## Who this is for

- one product with a few visible versions
- simple latest/development/archive routing
- maybe one mounted subtree for generated or imported docs

## Smallest useful mental model

Keep one component or one main artifact in focus, but make version and redirect
behavior explicit instead of relying on ad-hoc permalink changes.

For this size band, the important model shift is:

- treat public URLs as consumer-owned policy
- let the pipeline resolve canonical routes, aliases, and redirects
- inspect the staged route and redirect aggregates instead of guessing from
  source layout

## Read these first

1. [../how-to/model-versioning-and-redirects.md](../how-to/model-versioning-and-redirects.md)
2. [../how-to/inspect-staged-output-and-routes.md](../how-to/inspect-staged-output-and-routes.md)
3. [../how-to/http-server-config-how-to.md](../how-to/http-server-config-how-to.md)

## Ignore for now

Most small sites can defer:

- grouped components and group-level defaults
- provider snapshot integration
- translation linkage and localization
- advanced compatibility metadata

## Read this next when you grow

Move to [medium.md](medium.md) when the site has multiple artifacts, imported or
generated docs become normal, or publication planning/materialization becomes a
real step in the workflow.

## Deeper reference trail

- [../reference/flexible-component-publication.md](../reference/flexible-component-publication.md)
- [../reference/staged-output-contract.md](../reference/staged-output-contract.md)
- [../reference/security-and-trust-model.md](../reference/security-and-trust-model.md)