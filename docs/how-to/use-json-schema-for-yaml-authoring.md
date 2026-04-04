---
title: Use JSON Schema for YAML authoring help
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

Use the checked-in JSON Schema files under `schemas/` to get field completion,
required-field validation, and hover help while editing authored YAML files.

The schema files are generated from the same Pydantic models that validate
`site/components.yaml` and `site/component.yaml`. That means model docstrings
and Python `Field(description=...)` metadata are the source of truth for IDE
help text.

## Available schema files

- `schemas/site-pipeline-catalog-v1.schema.json` for `site/components.yaml`
- `schemas/site-pipeline-component-v1.schema.json` for `site/component.yaml`

## Regenerate the schema files

Run:

- `make schemas`

This rewrites the checked-in files under `schemas/` from the current Python
model definitions.

## Wire the schemas into your editor

For VS Code or other `yaml-language-server` based editors, map the schema files
to the authored YAML filenames. If you are editing a sibling consumer repo from
the same checkout, point the mapping at this repository's `schemas/` directory.

You can also use a per-file schema hint comment when your editor supports it,
for example with `yaml-language-server`:

- `# yaml-language-server: $schema=../buildish-site-pipeline/schemas/site-pipeline-catalog-v1.schema.json`
- `# yaml-language-server: $schema=../buildish-site-pipeline/schemas/site-pipeline-component-v1.schema.json`

## What the JSON Schema does not replace

The JSON Schema helps with local authoring feedback, but it does not replace
`site-pipeline check`. Cross-reference validation, duplicate detection, and
higher-order planning rules still require the normal pipeline validation pass.