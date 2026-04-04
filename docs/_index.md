---
title: Site Pipeline Documentation
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

Apache Buildish Site Pipeline reads docs files from one or more code projects,
whether they live in one monorepo or across multiple repositories, plus site
configuration such as `site/components.yaml`, checks that everything fits
together, and writes the result to `site/.stage/` for a renderer such as Hugo
or for later publishing steps.

The most important idea is simple: Site Pipeline prepares a site for rendering.
It does not try to be the renderer, theme layer, or hosting platform. A
renderer such as Hugo is the part that turns the staged Markdown into the final
styled website.

## What goes in and what comes out

- **You put in**:
  - Markdown pages and other docs files
  - release-version and branch-specific docs when your site publishes multiple
    versions at once
  - site configuration that says what should be published and where
  - optional release or version metadata from systems like GitHub
- **Site Pipeline does**:
  - validate the inputs
  - work out routes, versions, redirects, and publication paths
  - write a normalized site snapshot under `site/.stage/`
- **A renderer such as Hugo then uses**:
  - the staged page files under `site/.stage/content/`
  - the JSON metadata files under `site/.stage/data/`
  - `site/.stage/manifest.json` as the entry point into the staged output

## What Site Pipeline is

- a reusable staging pipeline for documentation sites
- a tool for assembling one site from multiple code projects, whether they live
  in one monorepo or in multiple repositories
- a tool for turning docs files and site config into one predictable output
  directory
- a tool that writes staged pages and JSON metadata for later rendering and
  publishing steps
- a tool that makes publication rules, version paths, routes, and redirects
  explicit and validated
- a tool designed to keep local development renderer-friendly, with
  `site-pipeline watch` keeping the staged output current for a renderer such as
  Hugo

## Local development workflow

- use `site-pipeline watch` to keep `site/.stage/` up to date while you edit
  docs, config, and versioned content
- keep using a renderer dev server such as `hugo serve` to turn that staged
  content into the local site you see in the browser
- the goal is not to replace renderer workflows, but to make them work cleanly
  with multi-project, multi-version documentation sites

## What Site Pipeline is not

- not a renderer or theme system
- not a CMS
- not a generic website builder
- not a hosting or deployment platform
- not a replacement for consumer-owned publication and release policy

## Good fit if

- your site needs a stable boundary between content preparation and rendering
- your site is assembled from multiple code projects, whether that is one
  monorepo or multiple repositories
- you have multiple components, artifacts, versions, or publication surfaces
- you need to publish release-version docs and branch-specific docs together in
  one site
- you want a developer-friendly local loop where `site-pipeline watch` and a
  renderer such as `hugo serve` work together
- you need redirects, aliases, canonical routes, or strong permalink continuity
- you need to mount generated or imported docs into one publication model
- you want deployment adapters to consume server-neutral staged metadata instead
  of reverse-engineering rendered output

## Probably not a fit if

- a single repository rendered directly by one site generator already solves the
  problem well enough
- you want a fully integrated renderer, theme, and hosting stack in one tool
- you do not need a separate staging boundary or explicit publication model

## Five-minute mental model

1. You provide docs files plus site configuration that says what should be
   published, including release-version docs or branch-specific docs when
   needed.
2. Site Pipeline checks paths, publication rules, and content shape.
3. It works out versions, routes, mounts, redirects, and optional provider
   metadata.
4. It writes a staged site under `site/.stage/`, including staged pages and
   JSON metadata files.
5. A renderer such as Hugo reads that staged output instead of reading source
   repositories directly, and `site-pipeline watch` can keep it fresh during
   local development.

If you want the deeper architecture explanation behind that model, start with
[architecture overview](architecture/architecture-overview.md).

## One concrete example

The smallest useful example in this docs set uses one component called `spark`
with one authored docs tree and one optional provider snapshot:

```text
site/
  components.yaml
  provider-snapshot.json
components/
  runtime/
    docs/
      releases/
        4.0.0/
          index.md
```

The catalog is still consumer-owned. For example:

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
    artifacts:
      - key: runtime
        source: runtime
        versioning:
          developmentRef: main
```

The normal first commands are:

```bash
site-pipeline check
site-pipeline build
```

After `build`, the renderer-facing output lands in `site/.stage/`:

```text
site/.stage/
  content/
  data/
    components.json
    content-index.json
    routes.json
  manifest.json
```

That staged tree is the durable boundary. Renderers and deployment adapters
should consume it instead of reading your repositories directly.

## Choose your path

- **I want to know whether this fits my site**
  - start with [getting started](getting-started/)
  - then read [architecture overview](architecture/architecture-overview.md)
- **I want to build a first working site**
  - start with [tiny](getting-started/tiny.md)
  - read [what a tiny site looks like](concepts/tiny-site-shape.md)
  - then follow [create a tiny site](how-to/create-a-tiny-site.md)
  - then inspect the result with
    [inspect staged output and routes](how-to/inspect-staged-output-and-routes.md)
- **I need the mental model before I follow a procedure**
  - start with [concepts](concepts/)
  - especially [what a tiny site looks like](concepts/tiny-site-shape.md) and
    [staged output and consumers](concepts/staged-output-and-consumers.md)
- **I need versions, redirects, and stable latest/development routes**
  - start with [small](getting-started/small.md)
  - then read
    [model versioning and redirects](how-to/model-versioning-and-redirects.md)
- **I need imported/generated docs or publication planning**
  - start with [medium](getting-started/medium.md)
  - then read
    [plan publication and materialization](how-to/plan-publication-and-materialization.md)
- **I need grouped components, provider data, or large-scale publication**
  - start with [large](getting-started/large.md) or
    [very-large](getting-started/very-large.md)
  - then read
    [integrate provider compatibility and translation data](how-to/integrate-provider-compatibility-and-translation-data.md)
- **I need to wire the staged output into a concrete renderer**
  - read [integrate with Hugo](how-to/integrate-with-hugo.md)
  - or [integrate with Jekyll](how-to/integrate-with-jekyll.md)
  - or [integrate with MkDocs](how-to/integrate-with-mkdocs.md)
- **I need exact contracts and schemas**
  - go to [reference](reference/)
  - especially [staged output contract](reference/staged-output-contract.md) and
    [API contract](reference/api-contract.md)
- **I maintain the implementation**
  - go to [maintenance](maintenance/)

## What this looks like in practice

If you want to see concrete shapes instead of starting from theory, use these
paths:

- [tiny getting-started guide](getting-started/tiny.md) for the smallest useful
  setup
- [what a tiny site looks like](concepts/tiny-site-shape.md) for the exact file
  layout, config shape, and first command sequence
- [create a tiny site](how-to/create-a-tiny-site.md) for the first working flow
- [staged output and consumers](concepts/staged-output-and-consumers.md) for
  manifest, front matter, and content-index examples
- [inspect staged output and routes](how-to/inspect-staged-output-and-routes.md)
  to see what the pipeline actually emits
- [staged output contract](reference/staged-output-contract.md) for the stable
  renderer-facing boundary

## Documentation sections

- [getting-started](getting-started/) for onboarding and size-band selection
- [concepts](concepts/) for plain-language models and concrete examples
- [how-to](how-to/) for task-oriented guides
- [architecture](architecture/) for system shape, rationale, and design examples
- [reference](reference/) for contracts, schemas, glossary, and trust-model docs
- [maintenance](maintenance/) for maintainer-facing internal guidance
- [v0](v0/) for the original tracked documentation set

## Natural next steps

- If you are new, start with [getting started](getting-started/).
- If you already know your site shape, jump straight to the matching size band.
- If you need the exact renderer boundary, read the
  [staged output contract](reference/staged-output-contract.md).
- If you want the current design explanation, read
  [architecture overview](architecture/architecture-overview.md).