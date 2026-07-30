---
title: Inspect staged output and routes
description: "Use this guide after a successful build when you want to understand what the pipeline actually staged and which public routes it resolved."
weight: 17
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

## Start with the manifest

Always read `manifest.json` first.

For a tiny `spark` example, the important part looks like this:

```json
{
  "command": "build",
  "roots": {
    "content": "content",
    "static": "static",
    "data": "data"
  },
  "dataFiles": {
    "components": "data/components.json",
    "routes": "data/routes.json",
    "redirects": "data/redirects.json",
    "contentIndex": "data/content-index.json"
  }
}
```

It is the authoritative entry point for:

- the top-level staged roots
- which aggregate data files are present
- where the route and redirect inventories live for this stage

Use it as a lookup file and contract entry point. Do not treat it as ordinary
renderer data. It is the finalized stage marker and may change on each
successful stage refresh even when the interesting renderer-facing data files do
not.

## Then inspect the route surfaces

The most useful next files are usually:

- the path referenced by `manifest.dataFiles.routes`
- the path referenced by `manifest.dataFiles.redirects`

Use them to answer different questions:

- `routes.json` tells you which public routes the stage owns
- `redirects.json` tells you which requests should redirect and where they go

One concrete `routes.json` item looks like this:

```json
{
  "originKey": "docs",
  "baseUrl": "https://docs.example.org",
  "path": "/spark/releases/4.0.0/",
  "url": "https://docs.example.org/spark/releases/4.0.0/",
  "componentSlug": "spark",
  "artifactKey": "runtime",
  "section": "released",
  "routeKind": "context",
  "targetId": "released:spark:runtime:4.0.0"
}
```

`section` tells you which publication surface the route belongs to. `routeKind`
is the route class, such as `published`, `context`, or `alias`. The separate
`canonical` flag tells you which published route is preferred when more than one
route points at the same target.

One concrete `redirects.json` item looks like this:

```json
{
  "fromUrl": "https://docs.example.org/spark/development/docs/",
  "toUrl": "https://docs.example.org/spark/releases/4.0.0/",
  "status": 302,
  "sourceKind": "catalog"
}
```

`sourceKind` tells you why the redirect exists. The built-in staging flow uses
values such as `catalog` for authored publication redirects and `withdrawal` for
withdrawn-release redirects.

## Inspect one staged page

Open a staged page under `content/` and look for the injected `pipeline` front
matter:

```yaml
pipeline:
  component:
    slug: spark
  page:
    kind: release-page
    path: /spark/releases/4.0.0
    canonicalUrl: https://docs.example.org/spark/releases/4.0.0/
    version:
      kind: released
      label: 4.0.0
```

That is the bridge between one page file and the normalized publication model.

## Then inspect cross-page discovery

`content-index.json` gives consumers a page inventory they can search without
scanning the whole content tree:

```json
{
  "componentSlug": "spark",
  "artifactKey": "runtime",
  "pageKind": "release-page",
  "path": "/spark/releases/4.0.0",
  "sourcePath": "components/runtime/docs/releases/4.0.0/index.md",
  "versionKind": "released",
  "versionLabel": "4.0.0",
  "provider": "github"
}
```

## Keep the contract boundary in mind

The staged tree is the downstream contract. Renderers, deployment adapters, and
audit tools should integrate against the stage root instead of reading internal
Python objects or arbitrary source repositories.

## Useful command-line checks

```bash
cat site/.stage/manifest.json
cat site/.stage/data/routes.json
cat site/.stage/data/content-index.json
```

## Typical next steps

- generate HTTP-server or CDN config from the route and redirect metadata
- validate that the expected latest, archive, or alias routes exist
- inspect page front matter under the staged content tree

## Read this next

- [../concepts/staged-output-and-consumers.md](../../concepts/staged-output-and-consumers/)
- [http-server-config-how-to.md](../http-server-config-how-to/)
- [staged output contract](../../development/reference/staged-output-contract/)
- [pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
