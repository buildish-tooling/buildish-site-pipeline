---
title: Medium sites
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

This page is for product families with multiple visible publication surfaces,
common generated or imported docs, and a real planning/materialization step.

## Who this is for

- one product plus tools or subprojects
- multiple visible versions or lifecycle states
- imported docs, generated refs, or mounted content are common

## Smallest useful mental model

At this size, the pipeline is no longer just a file copier. It is a boundary
between publication policy, local materialized inputs, and stable staged output.

You will usually need to think about:

- components versus artifacts
- shared defaults across related publication surfaces
- planning which contexts should exist before staging starts
- lifecycle and publication state in addition to plain route layout

## Read these first

1. [../how-to/plan-publication-and-materialization.md](../how-to/plan-publication-and-materialization.md)
2. [../how-to/model-versioning-and-redirects.md](../how-to/model-versioning-and-redirects.md)
3. [../architecture/source-resolution-and-materialization.md](../architecture/source-resolution-and-materialization.md)

## Ignore for now

You can still often postpone:

- cross-component compatibility relationships
- provider snapshot integration if authored metadata is enough
- localization and translation linkage

## Read this next when you grow

Move to [large.md](large.md) when you need grouped components, strong
compatibility relationships, or provider-enriched publication state across a
larger ecosystem.

## Deeper reference trail

- [../reference/flexible-component-publication.md](../reference/flexible-component-publication.md)
- [../reference/validation-and-check.md](../reference/validation-and-check.md)
- [../reference/pipeline-model-schema-reference.md](../reference/pipeline-model-schema-reference.md)