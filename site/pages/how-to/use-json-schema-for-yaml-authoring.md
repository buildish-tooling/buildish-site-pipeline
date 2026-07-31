---
title: Use JSON Schema for Site Pipeline file contracts
description: "Use local Site Pipeline schema exports for completion, hover help, and early validation, and understand their intended canonical URLs."
weight: 23
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

Use the JSON Schema exports when you want faster feedback while editing Site
Pipeline inputs. A good editor can use them for:

- field completion
- required-field validation
- hover help for documented fields
- early detection of misspelled or misplaced keys

## Start with the current schema filenames

Most users only need the schemas for the authored input files:

- `site/catalog.yaml`: `catalog-v1.schema.json`
- `site/component.yaml`: `component-v1.schema.json`
- optional `site/provider-snapshot.json`: `provider-snapshot-v1.schema.json`

The generated schemas are checked into the Site Pipeline source tree under
`site/pages/schemas/`. The Buildish site does not publish those files yet, so
the corresponding `buildish.org` URLs are not currently downloadable.

Each schema already uses its intended canonical URL as its `$id`. Once schema
publication is in place, the authored-input URLs will be:

- `site/catalog.yaml`: `https://buildish.org/components/site-pipeline/schemas/catalog-v1.schema.json`
- `site/component.yaml`: `https://buildish.org/components/site-pipeline/schemas/component-v1.schema.json`
- optional `site/provider-snapshot.json`: `https://buildish.org/components/site-pipeline/schemas/provider-snapshot-v1.schema.json`

Treat those URLs as contract identifiers until publication is available, not
as working download locations.

## Add schema hints to authored YAML

If your editor supports `yaml-language-server`, add a schema hint comment at
the top of each authored YAML file. Until the canonical URLs are published,
point the hint at a local schema file. For example, if you copy the schemas you
use into `site/schemas/`, refresh those copies whenever you update Site
Pipeline.

For `site/catalog.yaml`:

```yaml
# yaml-language-server: $schema=schemas/catalog-v1.schema.json
schemaVersion: 1
site: {}
```

For `site/component.yaml`:

```yaml
# yaml-language-server: $schema=schemas/component-v1.schema.json
schemaVersion: 1
component:
  slug: spark
```

If you edit `site/provider-snapshot.json` directly, use your editor's JSON
schema-mapping feature to associate that filename with a local copy of
`provider-snapshot-v1.schema.json`.

## Use the schemas as contract references

The checked-in schema exports are also useful outside the editor:

- CI checks can validate `manifest.json`, `data/components.json`, or
  `data/routes.json` against a matching local schema file
- downstream tools can use each schema's `$id` as the stable
  machine-readable contract identifier
- after publication is available, teams can share one canonical URL across
  multiple repositories instead of relying on local relative paths

Examples:

- [`manifest.json`](../../schemas/stage-manifest-v1.schema.json)
- [`data/components.json`](../../schemas/components-data-v1.schema.json)
- [`data/routes.json`](../../schemas/routes-data-v1.schema.json)

Links to all JSON schema files can be found in the [schema reference](../../development/reference/pipeline-model-schema-reference/).

## What schemas do not replace

JSON Schema is good at file-shape validation, but it does not replace
`site-pipeline check`.

You still need the normal validation pass for:

- cross-reference checks across files
- duplicate or conflicting publication rules
- provider-data consistency checks
- higher-order planning and staging rules

Use schemas for fast local feedback, then run `site-pipeline check` before you
treat the configuration as valid.

## Read this next

- [create a tiny site](../create-a-tiny-site/)
- [pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
- [provider snapshot schema](../../development/reference/provider-snapshot-schema/)
