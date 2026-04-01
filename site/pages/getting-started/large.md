---
title: Large sites
description: "This page is for platform-style sites with many modules, sibling projects, or extensions that share publication policy but still need explicit routing, lifecycle, and compatibility behavior."
weight: 14
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

## Who this is for

- one platform plus many modules or sibling projects
- several active release lines
- grouped publication policy and compatibility rules matter

## Smallest working shape

At this size, the site is an ecosystem rather than a single product. The key
shift is to treat publication defaults, route ownership, compatibility metadata,
and provider enrichment as first-class modeled inputs.

One concrete starter layout is:

```text
site/
  catalog.yaml
  provider-snapshot.json
components/
  spark/
    docs/
      index.md
      releases/
        4.0.0/
          index.md
  operator/
    docs/
      index.md
      releases/
        1.2.0/
          index.md
```

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
  spark:
    localDir: components/spark
  operator:
    localDir: components/operator
groups:
  streaming:
    displayName: Streaming
    pathPrefix: /platform/
components:
  - slug: spark
    group: streaming
    content:
      source: spark
    publication:
      pathSegment: spark
    compatibility:
      - subjectRef: component:spark
        targetRef: component:spark-operator
        relation: testedWith
        notes: Spark runtime docs assume the matching operator line.
    artifacts:
      - key: runtime
        source: spark
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
  - slug: spark-operator
    group: streaming
    content:
      source: operator
    publication:
      pathSegment: spark-operator
    artifacts:
      - key: operator
        source: operator
        versioning:
          developmentRef: main
          tagPattern: ^operator-v.*$
        publicationSelection:
          development: true
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: "1.2"
              maintenanceRef: maintenance/1.2
              latest: "1.2.0"
          releases:
            - version: "1.2.0"
```

One representative `site/provider-snapshot.json` then enriches release state
without taking over route ownership:

```yaml
schemaVersion: 1
providers:
  - key: github
    type: githubReleases
    fetchedAt: 2026-04-03T00:00:00Z
records:
  - provider: github
    kind: released
    componentSlug: spark
    artifactKey: runtime
    version: 4.0.0
    tag: v4.0.0
  - provider: github
    kind: released
    componentSlug: spark-operator
    artifactKey: operator
    version: 1.2.0
    tag: operator-v1.2.0
```

The first commands are usually:

```bash
site-pipeline check
site-pipeline build
```

After `build`, inspect at least:

```text
site/.stage/
  data/components.json
  data/compatibility.json
  data/releases.json
  data/routes.json
```

For this size band, the important sanity check is that the grouped publication
policy is obvious in `data/routes.json`, while compatibility and provider data
show up in their own emitted aggregates instead of being hidden in route hacks.

## Read these first

1. [../how-to/organize-grouped-components-and-publication-policy.md](../../how-to/organize-grouped-components-and-publication-policy/)
2. [../how-to/plan-publication-and-materialization.md](../../how-to/plan-publication-and-materialization/)
3. [../how-to/integrate-provider-compatibility-and-translation-data.md](../../how-to/integrate-provider-compatibility-and-translation-data/)

## Usually still background material

Only skip localization and provider topics if the site truly does not need them.
For many large sites, those topics are already close to the critical path.

## Read this next when you grow

Move to [very-large.md](../very-large/) when the site spans many repositories or
product families and needs stronger operational boundaries, localization policy,
or very large redirect inventories.

## Deeper reference trail

- [flexible component publication](../../development/reference/flexible-component-publication/)
- [provider snapshot schema](../../development/reference/provider-snapshot-schema/)
- [provider to staged metadata mapping](../../development/reference/provider-to-staged-metadata-mapping/)
- [security and trust model](../../development/reference/security-and-trust-model/)
