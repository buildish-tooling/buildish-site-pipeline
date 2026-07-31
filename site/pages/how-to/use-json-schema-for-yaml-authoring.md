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

Use the JSON Schema exports when you want feedback while editing Site Pipeline
inputs, before a full pipeline check. A schema-aware editor can provide:

- field completion
- required-field validation
- hover help for documented fields
- early detection of misspelled or misplaced keys

## Choose the schema for the file

Most users only need the schemas for the authored input files:

- `site/catalog.yaml`: `catalog-v1.schema.json`
- `site/component.yaml`: `component-v1.schema.json`
- optional `site/provider-snapshot.json`: `provider-snapshot-v1.schema.json`

The exports are checked into the Site Pipeline source tree under
`site/pages/schemas/`. The Buildish site does not publish those files yet, so
the corresponding `buildish.org` URLs are not currently downloadable. For now,
copy the schemas you use into the repository that contains each YAML file and
refresh those copies when you update Site Pipeline.

Each schema already uses its intended canonical URL as its `$id`. Once schema
publication is in place, the authored-input URLs will be:

- `site/catalog.yaml`: `https://buildish.org/components/site-pipeline/schemas/catalog-v1.schema.json`
- `site/component.yaml`: `https://buildish.org/components/site-pipeline/schemas/component-v1.schema.json`
- optional `site/provider-snapshot.json`: `https://buildish.org/components/site-pipeline/schemas/provider-snapshot-v1.schema.json`

Treat those URLs as contract identifiers until publication is available, not
as working download locations. A schema's `$id` identifies its contract; it
does not prove that the URL is already serving the schema.

## Put local schemas next to each authored contract

This is one concrete multi-repository arrangement:

```text
workspace/
├── buildish-site/
│   └── site/
│       ├── catalog.yaml
│       ├── provider-snapshot.json
│       └── schemas/
│           ├── catalog-v1.schema.json
│           └── provider-snapshot-v1.schema.json
└── components/
    └── runtime/
        └── site/
            ├── component.yaml
            └── schemas/
                └── component-v1.schema.json
```

The directory name `schemas` is a local convention, not a pipeline input
requirement. What matters is that the editor directive resolves to the copied
file. Keeping a component's schema in the component repository also avoids a
fragile editor dependency on the operator's workspace layout.

## Add schema hints to authored YAML

If your editor supports `yaml-language-server`, add a modeline comment near the
top of each authored YAML file. The path after `$schema=` is resolved relative
to the YAML file containing the comment, not relative to the shell's current
directory or the Site Pipeline checkout.

The modeline is a YAML comment interpreted by editor tooling. It is not a
`$schema` field in the YAML document. Adding a real `$schema:` mapping key would
change the authored input and will be rejected because it is not part of these
file contracts.

For `site/catalog.yaml`:

<!-- test:schema-catalog -->
```yaml
# yaml-language-server: $schema=schemas/catalog-v1.schema.json
schemaVersion: 1
site: {}
```

For `site/component.yaml`:

<!-- test:schema-component -->
```yaml
# yaml-language-server: $schema=schemas/component-v1.schema.json
schemaVersion: 1
component:
  slug: spark
```

With the tree above, the catalog directive resolves to
`buildish-site/site/schemas/catalog-v1.schema.json`, while the component
directive resolves to
`components/runtime/site/schemas/component-v1.schema.json`.

`site/provider-snapshot.json` is JSON rather than YAML. Associate it with the
local `provider-snapshot-v1.schema.json` through your editor's JSON
schema-mapping settings. Editor configuration syntax varies, so this guide does
not prescribe one mapping format.

This repository is also the component that publishes the schema files, so its
own `site/component.yaml` uses
`pages/schemas/component-v1.schema.json`. That path is likewise relative to the
YAML file; it reflects this repository's real tree rather than a special
pipeline rule.

## Switch to canonical URLs after publication

Once the canonical files are actually served, the catalog modeline can become:

```yaml
# yaml-language-server: $schema=https://buildish.org/components/site-pipeline/schemas/catalog-v1.schema.json
schemaVersion: 1
site: {}
```

Until then, keep using the local path. A team that wants reproducible editor and
CI behavior may also choose to retain versioned local copies after publication.

## Use the schemas as contract references

The checked-in schema exports are also useful outside the editor:

- CI checks can validate `manifest.json`, `data/components.json`, or
  `data/routes.json` against a matching local schema file
- downstream tools can use each schema's `$id` as the stable
  machine-readable contract identifier
- after publication is available, teams can share one canonical URL across
  multiple repositories instead of relying on local relative paths

Local examples from this component checkout:

- [`manifest.json`](../../schemas/stage-manifest-v1.schema.json)
- [`data/components.json`](../../schemas/components-data-v1.schema.json)
- [`data/routes.json`](../../schemas/routes-data-v1.schema.json)

Links to all JSON schema files can be found in the
[unreleased development schema reference](../../development/reference/pipeline-model-schema-reference/).

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

## Troubleshooting

### The editor offers no completion or validation

Confirm that the file is in YAML mode, the editor has YAML Schema support, and
the modeline is a comment near the top of the file. Then resolve the modeline
path starting from the YAML file's directory and verify that the schema file
exists there.

### The editor cannot load the schema

Check filename spelling and version first. `catalog-v1.schema.json` and
`component-v1.schema.json` are different contracts. A relative path is not
resolved from the workspace root. A canonical `buildish.org` URL will also fail
until schema publication is deployed; use a local copy in the meantime.

### Validation reports `$schema` as an unknown field

Use `# yaml-language-server: $schema=...`, including the leading `#`. A YAML
field written as `$schema: ...` is input data rather than an editor directive.

### The schema accepts the file but `site-pipeline check` fails

That can be correct. JSON Schema validates one document's shape. The pipeline
also validates relationships between files, source paths, duplicate routes,
provider consistency, and other planning rules.

## Read this next

- [create a tiny site](../create-a-tiny-site/)
- [unreleased development pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
- [unreleased development provider snapshot schema](../../development/reference/provider-snapshot-schema/)
