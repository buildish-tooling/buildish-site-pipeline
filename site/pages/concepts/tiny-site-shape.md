---
title: What a tiny site looks like
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

This page shows the smallest concrete example thread used across the user-facing
docs.

## Repository shape

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

`site/catalog.yaml` is the consumer-owned entry point. One minimal versioned
example looks like this:

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
```

The optional `site/provider-snapshot.json` enriches version metadata without
making the renderer talk to providers directly.

## Authored page shape

The authored page can stay ordinary Markdown:

```markdown
---
title: Spark 4.0.0 release notes
---

Hello from the first staged page.
```

## First commands

Run these from the workspace root:

```bash
site-pipeline check
site-pipeline build
```

Use `check` when you want validation without mutating `site/.stage/`. Use
`build` when you want the content tree and aggregate data written.

## What appears after build

```text
site/.stage/
  content/spark/releases/4.0.0/index.md
  data/components.json
  data/content-index.json
  data/routes.json
  data/redirects.json
  manifest.json
```

That output is the important boundary:

- authored files stay in your repos
- staged files become consumer input for renderers and deployment adapters
- component-owned staged paths follow the same resolved public hierarchy that the
  route inventory publishes
- aggregate JSON files tell downstream tools which public routes, redirects,
  pages, and metadata the stage owns

## What matters at this size

- stable component identity like `spark`
- one clear docs root
- one publication mount path such as `/spark/`
- using `manifest.json` as the entry point into the stage root

## What you can ignore for now

- grouped components
- localization and translation linkage
- compatibility metadata
- advanced publication planning

## Read next

- [../how-to/create-a-tiny-site.md](../how-to/create-a-tiny-site.md)
- [staged-output-and-consumers.md](staged-output-and-consumers.md)
- [../getting-started/tiny.md](../getting-started/tiny.md)