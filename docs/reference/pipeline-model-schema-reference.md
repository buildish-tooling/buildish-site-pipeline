---
title: "Pipeline model schema reference"
description: "This reference is generated from the Site Pipeline Pydantic models and checked-in reference metadata. Do not edit it by hand; regenerate it with `make schemas`."
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

This reference describes the current public contracts exposed by the Site Pipeline model layer.
It covers authored inputs, provider inputs, pipeline-emitted outputs, shared scalars, enums, and the detailed field rules for each typed contract.

## How to read this reference

- file-contract pages identify the stable on-disk file for each root contract, if applicable
- field names are shown in their wire-format aliases
- type, enum, and scalar names link to their definitions on the detailed pages
- schema files link to the published JSON Schema contract for the matching root type

## Reference pages

- [File contract index](../pipeline-file-contract-index/) — authored, provider, and emitted file/root contract tables.
- [Shared types reference](../pipeline-shared-types-reference/) — shared scalar aliases and enums.
- [Authored input types](../pipeline-authored-input-reference/) — Consumer-owned and component-owned authored contract models.
- [Provider input types](../pipeline-provider-input-reference/) — Normalized provider snapshot contracts consumed by the pipeline.
- [Planning and stage-contract types](../pipeline-planning-and-stage-contract-reference/) — Pipeline-emitted planning, diagnostics, and stage-manifest contracts.
- [Staged front matter types](../pipeline-staged-front-matter-reference/) — Front matter and page-level metadata emitted into staged content.
- [Staged aggregate metadata types](../pipeline-staged-aggregate-metadata-reference/) — Public aggregate JSON contracts emitted under `data/`.
- [Incremental bookkeeping types](../pipeline-incremental-bookkeeping-reference/) — Pipeline-internal emitted bookkeeping contracts stored under `data/_pipeline/`.

## Coverage notes

- generated schema files: `24`
- stable contract pages are split by contract family to keep navigation and review manageable.

