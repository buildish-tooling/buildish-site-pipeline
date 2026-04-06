---
title: Create a tiny site
weight: 16
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

Use this guide when you want the smallest useful Site Pipeline setup: one
consumer-owned site catalog, one component, and one staged output.

## Create the smallest useful tree

Start with this workspace shape:

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

The provider snapshot is optional. Keep it when you want provider-enriched
metadata in staged page front matter and aggregate files.

## Write the catalog

Create `site/catalog.yaml`:

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

If you want provider-enriched version metadata in the first build, create
`site/provider-snapshot.json`:

```json
{
  "schemaVersion": 1,
  "providers": [{"key": "github", "type": "githubReleases", "fetchedAt": "2026-04-03T00:00:00Z"}],
  "records": [
    {"provider": "github", "kind": "development", "componentSlug": "spark", "artifactKey": "runtime", "ref": "main"},
    {"provider": "github", "kind": "lineHead", "componentSlug": "spark", "artifactKey": "runtime", "releaseLine": "4.0", "ref": "maintenance/4.0"},
    {"provider": "github", "kind": "released", "componentSlug": "spark", "artifactKey": "runtime", "version": "4.0.0", "tag": "v4.0.0"}
  ]
}
```

## Add one authored page

Create `components/runtime/docs/releases/4.0.0/index.md`:

```markdown
---
title: Spark 4.0.0 release notes
---

Hello from the first staged page.
```

## Validate and build

Run these from the workspace root:

```bash
site-pipeline check
site-pipeline build
```

Those defaults assume the catalog lives at `site/catalog.yaml`. If your site
catalog is in a different repository or you invoke the CLI from outside the
workspace root, pass both paths explicitly:

```bash
site-pipeline check --workspace-root /workspace --catalog /workspace/buildish/site/catalog.yaml
site-pipeline build --workspace-root /workspace --catalog /workspace/buildish/site/catalog.yaml
```

With that split, authored relative paths from the catalog still resolve from
`--workspace-root`, while `.stage`, `.site-pipeline-work`, and the default
provider snapshot stay next to the selected catalog file.

If you want a machine-readable build report for automation, use:

```bash
site-pipeline build --report-format json --report-schema-version 1
```

## What to decide early

Even for a tiny site, decide these explicitly:

- the stable component identity
- which content roots belong to the component repository
- which content belongs to the consumer-owned site layer instead

That keeps component identity separate from future publication layout changes.

## Inspect the first successful result

After `build`, inspect these paths first:

```text
site/.stage/manifest.json
site/.stage/content/components/spark/contexts/releases/4.0.0/index.md
site/.stage/data/routes.json
site/.stage/data/redirects.json
site/.stage/data/content-index.json
```

One staged page now carries normalized pipeline metadata in its front matter:

```yaml
pipeline:
  component:
    slug: spark
  page:
    kind: release-page
    path: /spark/releases/4.0.0
    provider:
      key: github
    version:
      kind: released
      label: 4.0.0
```

## What success looks like

You are in a good starting state when:

- the pipeline produces one coherent stage root
- `manifest.json` is present and readable
- staged pages and assets are separated from source layout details
- a renderer can consume the stage root without reading repositories directly

## Read this next

- [../concepts/staged-output-and-consumers.md](../concepts/staged-output-and-consumers.md)
- [inspect-staged-output-and-routes.md](inspect-staged-output-and-routes.md)
- [flexible component publication](/docs/reference/flexible-component-publication/)
- [staged output contract](/docs/reference/staged-output-contract/)