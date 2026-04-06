---
title: Tiny sites
description: "This page is for sites with one component, one main docs tree, and only a small amount of lifecycle or routing complexity."
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

## Who this is for

- one component repository
- one primary docs tree
- little or no version-history surface

## Smallest working shape

Start with one consumer-owned catalog, one component source tree, and one staged
output produced by `site-pipeline build`.

The smallest useful concrete shape is:

```text
site/
  catalog.yaml
  provider-snapshot.json
components/
  runtime/
    docs/
      releases/
        4.0.0/
          index.md
```

The smallest useful mental model is still simple:

- `site/catalog.yaml` tells the pipeline which content participates
- component source trees hold the authored docs that participate
- the pipeline stages content into a stable output tree for a renderer or other
  downstream consumer

One representative `site/catalog.yaml` looks like this:

```yaml
schemaVersion: 1
defaults:
  docsRoot: docs
  publication:
    origin: docs
origins:
  docs:
    baseUrl: https://docs.example.org
sources:
  runtime:
    localDir: components/runtime
components:
  - slug: spark
    content:
      source: runtime
    publication:
      mountPath: /spark/
```

The first commands are:

```bash
site-pipeline check
site-pipeline build
```

Those examples assume you run from the workspace root and keep the catalog at
`site/catalog.yaml`. If you run from somewhere else or keep the catalog in a
different repository, pass both selection flags explicitly, for example:

```bash
site-pipeline build --workspace-root /workspace --catalog /workspace/buildish/site/catalog.yaml
```

In that split layout, authored relative paths still resolve from
`--workspace-root`, while `.stage`, `.site-pipeline-work`, and the default
provider snapshot stay next to the selected catalog.

After `build`, expect at least:

```text
site/.stage/
  content/
  data/
  manifest.json
```

## Read these first

1. [../concepts/tiny-site-shape.md](../../concepts/tiny-site-shape/)
2. [../concepts/staged-output-and-consumers.md](../../concepts/staged-output-and-consumers/)
3. [../how-to/create-a-tiny-site.md](../../how-to/create-a-tiny-site/)
4. [../how-to/inspect-staged-output-and-routes.md](../../how-to/inspect-staged-output-and-routes/)
5. [staged output contract](/components/site-pipeline/development/reference/staged-output-contract/)

## Ignore for now

You can usually ignore these until the site grows:

- provider snapshots as a required dependency, even if you later use them as an
  optional enrichment input
- grouped components
- compatibility metadata
- localization and translation linkage
- advanced publication selection and materialization strategy

## Read this next when you grow

Move to [small.md](../small/) when the site adds stable version navigation,
redirects, or one mounted imported/generated docs subtree.

## Deeper reference trail

- [flexible component publication](/components/site-pipeline/development/reference/flexible-component-publication/)
- [pipeline model schema reference](/components/site-pipeline/development/reference/pipeline-model-schema-reference/)
