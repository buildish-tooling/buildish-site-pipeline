---
title: Tiny sites
weight: 11
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

This page is for sites with one component, one main docs tree, and only a small
amount of lifecycle or routing complexity.

## Who this is for

- one component repository
- one primary docs tree
- little or no version-history surface

## Smallest working shape

Start with one consumer-owned catalog, one component metadata file, and one
staged output produced by `site-pipeline build`.

The smallest useful mental model is:

- `site/components.yaml` tells the pipeline which content participates
- `site/component.yaml` describes component-owned content roots and identity
- the pipeline stages content into a stable output tree for a renderer or other
  downstream consumer

## Read these first

1. [../how-to/create-a-tiny-site.md](../how-to/create-a-tiny-site.md)
2. [../how-to/inspect-staged-output-and-routes.md](../how-to/inspect-staged-output-and-routes.md)
3. [../reference/staged-output-contract.md](../reference/staged-output-contract.md)

## Ignore for now

You can usually ignore these until the site grows:

- provider snapshots
- grouped components
- compatibility metadata
- localization and translation linkage
- advanced publication selection and materialization strategy

## Read this next when you grow

Move to [small.md](small.md) when the site adds stable version navigation,
redirects, or one mounted imported/generated docs subtree.

## Deeper reference trail

- [../reference/flexible-component-publication.md](../reference/flexible-component-publication.md)
- [../reference/pipeline-model-schema-reference.md](../reference/pipeline-model-schema-reference.md)