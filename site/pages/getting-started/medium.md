---
title: Medium sites
description: "This page is for product families with multiple visible publication surfaces, common generated or imported docs, and a real planning/materialization step."
weight: 13
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

- one product plus tools or subprojects
- multiple visible versions or lifecycle states
- imported docs, generated refs, or mounted content are common

## Smallest working shape

At this size, the pipeline is no longer just a file copier. It is a boundary
between publication policy, local materialized inputs, and stable staged output.

One concrete starter layout is:

```text
site/
  catalog.yaml
  provider-snapshot.json
components/
  runtime/
    docs/
      runtime/
        guide/
          index.md
        releases/
          4.0.0/
            guide/
              index.md
  api/
    docs/
      reference/
        index.md
      releases/
        4.0.0/
          reference/
            index.md
```

You will usually need to think about:

- components versus artifacts
- shared defaults across related publication surfaces
- planning which contexts should exist before staging starts
- lifecycle and publication state in addition to plain route layout

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
  api:
    localDir: components/api
components:
  - slug: spark
    content:
      source: runtime
    publication:
      mountPath: /spark/
    artifacts:
      - key: runtime
        source: runtime
        docsRoot: docs/runtime
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
        publicationSelection:
          development: true
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: "4.0"
              maintenanceRef: maintenance/4.0
              latest: "4.0.0"
          releases:
            - version: "4.0.0"
      - key: api
        source: api
        docsRoot: docs
        versioning:
          developmentRef: main
          tagPattern: ^api-v.*$
        publicationSelection:
          development: true
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: "4.0"
              maintenanceRef: maintenance/4.0
              latest: "4.0.0"
          releases:
            - version: "4.0.0"
```

That is the smallest useful medium-site packet because it already makes three
important things explicit:

- one public component route can carry several independently versioned artifacts
- `provider-snapshot.json` tells planning which development and release contexts
  actually exist before staging starts
- staged output is something you inspect directly, not something you infer from
  the source tree alone

The first commands are usually:

```bash
site-pipeline plan
site-pipeline check
site-pipeline build
```

After `build`, inspect at least:

```text
site/.stage/
  content/spark/development/guide/index.md
  content/spark/development/reference/index.md
  content/spark/releases/4.0.0/guide/index.md
  content/spark/releases/4.0.0/reference/index.md
  data/content-index.json
  data/routes.json
```

## Read these first

1. [../how-to/plan-publication-and-materialization.md](../how-to/plan-publication-and-materialization/)
2. [../how-to/model-versioning-and-redirects.md](../how-to/model-versioning-and-redirects/)
3. [../architecture/source-resolution-and-materialization.md](../architecture/source-resolution-and-materialization/)

## Ignore for now

You can still often postpone:

- cross-component compatibility relationships
- provider snapshot integration if authored metadata is enough
- localization and translation linkage

## Read this next when you grow

Move to [large.md](large/) when you need grouped components, strong
compatibility relationships, or provider-enriched publication state across a
larger ecosystem.

## Deeper reference trail

- [flexible component publication](/components/site-pipeline/development/reference/flexible-component-publication/)
- [validation and check](/components/site-pipeline/development/reference/validation-and-check/)
- [pipeline model schema reference](/components/site-pipeline/development/reference/pipeline-model-schema-reference/)
