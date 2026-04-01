---
title: How-to Guides
description: "This section contains task-oriented guides for common site-pipeline workflows."
weight: 15
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

Start with [Getting Started](../getting-started/) if you first need the core
workflow or help choosing a publication shape.

If you need the mental model and concrete example shapes before following a
procedure, read [Concepts](../concepts/) first.

## Build and inspect a first site

- [Create a tiny site](create-a-tiny-site/) from one catalog and one authored
  page.
- [Inspect staged output and routes](inspect-staged-output-and-routes/) after a
  successful build.

## Model publication and growth

- [Model versioning and redirects](model-versioning-and-redirects/) when public
  routes must remain stable across releases.
- [Plan publication and materialization](plan-publication-and-materialization/)
  when staging depends on selected versions or imported inputs.
- [Organize grouped components and publication policy](organize-grouped-components-and-publication-policy/)
  when several components share public policy.
- [Integrate provider, compatibility, and translation data](integrate-provider-compatibility-and-translation-data/)
  for larger publication ecosystems.
- [Scale Site Pipeline operations](scale-site-pipeline-operations/) when source,
  route, or deployment inventories need explicit operational boundaries.

## Renderer integration guides

Use these guides when you already understand the staged output and now want to
wire it into a concrete renderer workflow:

- [integrate with Hugo](integrate-with-hugo/) — documented direct mounts
- [integrate with Roq](integrate-with-roq/) — documented consumer-side adapter
- [Jekyll integration](integrate-with-jekyll/) — planned-guide status page, not
  a turnkey recipe
- [MkDocs integration](integrate-with-mkdocs/) — planned-guide status page, not
  a turnkey recipe

## Deployment adapter guides

- [Create HTTP server configuration from staged metadata](http-server-config-how-to/)
  while keeping target-specific syntax downstream of the pipeline contract.

## Authoring and editor guides

Use these guides when you want faster feedback while editing catalogs and
component metadata or when you need the generated file-contract schemas:

- [Use JSON Schema for Site Pipeline file contracts](use-json-schema-for-yaml-authoring/)
