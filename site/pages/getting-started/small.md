---
title: Small sites
description: "This page is for one main product with a small visible release history and maybe one mounted API, generated reference tree, or imported docs subtree."
weight: 12
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

- one product with a few visible versions
- simple latest-release/development/archive routing
- maybe one mounted subtree for generated or imported docs

## Smallest working shape

Keep one component and one independently versioned artifact in focus, but make
the development, maintenance-line, and released contexts explicit. A small
versioned workspace can look like this:

```text
site/
  catalog.yaml
  provider-snapshot.json
components/
  runtime/
    docs/
      index.md
      maintenance/
        4.0/
          index.md
      releases/
        4.0.0/
          index.md
```

The catalog owns the public route policy and which contexts are selected:

```yaml
schemaVersion: 1
defaults:
  docsRoot: docs
  publication:
    origin: docs
site: {}
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
    artifacts:
      - key: runtime
        source: runtime
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
        publicationSelection:
          development: true
          lineHeads:
            mode: allAuthored
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

The provider snapshot must contain matching records for the selected contexts.
It enriches the authored identities; it does not choose the public paths:

```json
{
  "schemaVersion": 1,
  "providers": [
    {
      "key": "github",
      "type": "githubReleases",
      "fetchedAt": "2026-04-03T00:00:00Z"
    }
  ],
  "records": [
    {
      "provider": "github",
      "kind": "development",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "ref": "main"
    },
    {
      "provider": "github",
      "kind": "lineHead",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "releaseLine": "4.0",
      "ref": "maintenance/4.0"
    },
    {
      "provider": "github",
      "kind": "released",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "version": "4.0.0",
      "tag": "v4.0.0"
    }
  ]
}
```

Run:

```bash
site-pipeline check
site-pipeline build
```

## Inspect the result

The staged route inventory should include these target/path pairs:

```text
development:spark:runtime       /spark/development/
line-head:spark:runtime:4.0     /spark/development/4.0/
released:spark:runtime:4.0.0    /spark/releases/4.0.0/
```

The matching pages should appear below `site/.stage/content/spark/`, while
`data/routes.json`, `data/releases.json`, and `data/refs.json` provide the
cross-page views. Add aliases or redirects in the publication policy only when
another public path must resolve to one of these targets.

## Common failures

- A selected context without a matching provider record cannot be staged.
- A release record whose component, artifact, version, ref, or tag disagrees
  with the authored lifecycle fails validation.
- Two components or contexts that claim the same public route cause a collision.
- A redirect to an unselected typed target cannot be resolved.

## Read these first

1. [Model versioning and redirects](../../how-to/model-versioning-and-redirects/)
2. [Inspect staged output and routes](../../how-to/inspect-staged-output-and-routes/)
3. [Create HTTP server configuration](../../how-to/http-server-config-how-to/)

## Ignore for now

Most small sites can defer:

- grouped components and group-level defaults
- translation linkage and localization
- advanced compatibility metadata

## Read this next when you grow

Move to [Medium sites](../medium/) when the site has multiple artifacts,
imported or generated docs become normal, or publication planning and
materialization become a regular step in the workflow.

## Deeper unreleased development reference

- [flexible component publication](../../development/reference/flexible-component-publication/)
- [staged output contract](../../development/reference/staged-output-contract/)
- [security and trust model](../../development/reference/security-and-trust-model/)

These contracts describe unreleased development behavior and have not yet been
published as release documentation.
