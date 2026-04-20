---
title: Use JSON Schema for Site Pipeline file contracts
description: "Use the published schema URLs to get completion, hover help, and early validation while editing Site Pipeline inputs."
weight: 23
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

Use the published JSON Schema URLs when you want faster feedback while editing
Site Pipeline inputs. A good editor can use them for:

- field completion
- required-field validation
- hover help for documented fields
- early detection of misspelled or misplaced keys

## Start with the published schema URLs

Most users only need the schemas for the authored input files:

- `site/catalog.yaml`: `https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-catalog-v1.schema.json`
- `site/component.yaml`: `https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-component-v1.schema.json`
- optional `site/provider-snapshot.json`: `https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-provider-snapshot-v1.schema.json`

If you also validate generated JSON in automation, matching schemas are
published for stage outputs and CLI reports under:

- `https://buildish.apache.org/components/site-pipeline/schemas/`

## Add schema hints to authored YAML

If your editor supports `yaml-language-server`, add a schema hint comment at
the top of each authored YAML file.

For `site/catalog.yaml`:

```yaml
# yaml-language-server: $schema=https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-catalog-v1.schema.json
schemaVersion: 1
site: {}
```

For `site/component.yaml`:

```yaml
# yaml-language-server: $schema=https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-component-v1.schema.json
schemaVersion: 1
component:
  slug: spark
```

If you edit `site/provider-snapshot.json` directly, use your editor's JSON
schema-mapping feature to associate that filename with the published provider
snapshot schema URL.

## Use the schemas as contract references

The published schema URLs are also useful outside the editor:

- CI checks can validate `manifest.json`, `data/components.json`, or `data/routes.json` against the matching published schema
- downstream tools can treat those URLs as the stable machine-readable contract
- teams can share one schema URL across multiple repositories instead of relying on local relative paths

Examples:

- [`manifest.json`](/components/site-pipeline/schemas/site-pipeline-stage-manifest-v1.schema.json)
- [`data/components.json`](/components/site-pipeline/schemas/site-pipeline-components-data-v1.schema.json)
- [`data/routes.json`](/components/site-pipeline/schemas/site-pipeline-routes-data-v1.schema.json)

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
- [pipeline model schema reference](/components/site-pipeline/development/reference/pipeline-model-schema-reference/)
- [provider snapshot schema](/components/site-pipeline/development/reference/provider-snapshot-schema/)
