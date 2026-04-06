---
title: Use JSON Schema for Site Pipeline file contracts
description: "Use the checked-in JSON Schema files under `schemas/` to get field completion, required-field validation, hover help for authored YAML, and machine-readable contract files for staged outputs and reports."
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

The schema files are generated from the same Pydantic models that validate or
emit the pipeline's public file contracts. That means model docstrings and
Python `Field(description=...)` metadata are the source of truth for schema
help text.

## Available schema files

The generated files now cover:

- authored inputs such as `site/catalog.yaml`, `site/component.yaml`, and `site/provider-snapshot.json`
- machine-readable CLI reports such as the materialization, check, and stage-run JSON reports
- staged output contracts such as `manifest.json`, `data/*.json`, and `data/_pipeline/*.json`
- the reserved `pipeline` front matter namespace embedded into staged page files

Examples:

- `schemas/site-pipeline-catalog-v1.schema.json` for `site/catalog.yaml`
- `schemas/site-pipeline-component-v1.schema.json` for `site/component.yaml`
- `schemas/site-pipeline-stage-manifest-v1.schema.json` for `site/.stage/manifest.json`
- `schemas/site-pipeline-components-data-v1.schema.json` for `site/.stage/data/components.json`
- `schemas/site-pipeline-front-matter-namespace-v1.schema.json` for the staged page `pipeline` front matter namespace

## Regenerate the schema files

Run:

- `make schemas`

This rewrites the checked-in files under `schemas/` from the current Python
model definitions.

Each generated schema file also carries a canonical published `$id` under:

- `https://buildish.apache.org/components/site-pipeline/schemas/<filename>`

That same stable HTTPS path is also a good default for authored YAML
`yaml-language-server` schema hints. Local relative `$schema` refs still work
for local-only development, but the published URL is the stable contract
identifier that can be shared across repositories.

## Wire the schemas into your editor

For VS Code or other `yaml-language-server` based editors, map the schema files
to the authored YAML filenames. If you are editing a sibling consumer repo from
the same checkout, point the mapping at this repository's `schemas/` directory.

You can also use a per-file schema hint comment when your editor supports it,
for example with `yaml-language-server`:

- `# yaml-language-server: $schema=https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-catalog-v1.schema.json`
- `# yaml-language-server: $schema=https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-component-v1.schema.json`

## What the JSON Schema does not replace

The JSON Schema helps with local authoring feedback and downstream contract
inspection, but it does not replace `site-pipeline check`. Cross-reference
validation, duplicate detection, and higher-order planning rules still require
the normal pipeline validation pass.
