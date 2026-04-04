---
title: Staged output and consumers
weight: 14
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

The staged tree is the durable hand-off point between Site Pipeline and the
systems that render, serve, or audit the site.

## Start with manifest.json

After `site-pipeline build`, `site/.stage/manifest.json` tells downstream tools
where the important stage roots and aggregate files live:

```json
{
  "schemaVersion": 1,
  "command": "build",
  "roots": {
    "content": "content",
    "static": "static",
    "data": "data"
  },
  "dataFiles": {
    "components": "data/components.json",
    "routes": "data/routes.json",
    "contentIndex": "data/content-index.json"
  }
}
```

If a consumer does not know where to start, `manifest.json` is the answer.

## Staged pages carry pipeline front matter

Site Pipeline keeps authored content readable but adds normalized `pipeline`
metadata that downstream tooling can trust:

```yaml
pipeline:
  component:
    slug: spark
  page:
    kind: release-page
    path: /spark/development/docs/releases/4.0.0
    provider:
      key: github
    version:
      kind: released
      label: 4.0.0
      tag: v4.0.0
```

That means a renderer can read one staged page and still know which component,
publication surface, provider, and version context it belongs to.

## Aggregate files answer cross-page questions

Use aggregate files when you need answers that span more than one page:

- `data/routes.json` for public routes
- `data/redirects.json` for redirect behavior
- `data/components.json` for component-level publication metadata
- `data/content-index.json` for page discovery

For example, one `content-index.json` item looks like this:

```json
{
  "componentSlug": "spark",
  "artifactKey": "runtime",
  "pageKind": "release-page",
  "path": "/spark/development/docs/releases/4.0.0",
  "canonicalUrl": "https://docs.example.org/spark/development/docs/releases/4.0.0/",
  "sourcePath": "components/runtime/docs/releases/4.0.0/index.md",
  "versionKind": "released",
  "versionLabel": "4.0.0",
  "provider": "github"
}
```

## What consumers should not do

Downstream systems should not:

- inspect internal Python objects
- infer routing directly from repo layout
- fetch provider state on their own to reconstruct page metadata

They should use the staged output instead.

## Read next

- [../how-to/inspect-staged-output-and-routes.md](../how-to/inspect-staged-output-and-routes.md)
- [../reference/staged-output-contract.md](../reference/staged-output-contract.md)
- [../reference/api-contract.md](../reference/api-contract.md)