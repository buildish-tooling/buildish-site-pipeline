---
title: Organize grouped components and publication policy
description: "Use this guide when one docs estate starts behaving like an ecosystem with many components, artifacts, or publication surfaces that should share defaults."
weight: 20
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

## What to centralize

Keep these concerns in the consumer-owned catalog layer:

- origins and public base URLs
- group-level defaults
- publication path policy
- per-component or per-artifact publication overrides

That lets component repositories keep owning identity and content roots without
owning the final public URL design.

## Define a group only for shared public behavior

This group places related components below `/platform/` and gives renderers a
stable label. Each component supplies only its route segment:

```yaml
sources:
  spark:
    localDir: components/spark
  operator:
    localDir: components/operator
groups:
  streaming:
    displayName: Streaming
    pathPrefix: /platform/
    navigationSection: Streaming projects
components:
  - slug: spark
    group: streaming
    content:
      source: spark
    publication:
      pathSegment: spark
    artifacts: []
  - slug: spark-operator
    group: streaming
    content:
      source: operator
    publication:
      pathSegment: spark-operator
    artifacts: []
```

The resolved component roots are:

```text
/platform/spark/
/platform/spark-operator/
```

`data/components.json` retains the `streaming` group identity for navigation or
listing templates. `data/routes.json` remains authoritative for the public
paths.

## Apply defaults from broad to narrow

Use this order when deciding where a setting belongs:

1. Put site-wide origin and path-segment defaults in `defaults`.
2. Put policy shared only by a real component family in its `groups` entry.
3. Put component-specific route choices on the component.
4. Put independently versioned publication choices on the artifact.

The nearest explicit setting wins, but an override should express a real public
difference rather than mirror repository layout.

## Validate before adding content

After introducing or changing a group, run:

```bash
site-pipeline check
site-pipeline build
```

Inspect the two component entries and their routes before adding aliases,
redirects, releases, or mounted content. This makes it easier to identify which
inheritance layer created a surprising path.

## When to add another group

Add a group when it gives a clearer shared default layer. Do not add groups just
to mirror repository layout or organization charts.

Good reasons include a shared public prefix, navigation section, origin, or
ordering policy. If components share only ownership or repository location,
renderer navigation or source configuration is usually the better place to
express that relationship.

## Failure cases

- Two components that resolve to the same path fail route-ownership checks.
- A component that names an unknown group fails reference validation.
- A `pathSegment` must remain one segment; use the group's `pathPrefix` for the
  shared hierarchy.
- An explicit `mountPath` can bypass the group prefix, so use it only when that
  exception is intentional and review the resulting route inventory.

## Read this next

- [Plan publication and materialization](../plan-publication-and-materialization/)

For unreleased development contract details:

- [flexible component publication](../../development/reference/flexible-component-publication/)
- [pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
