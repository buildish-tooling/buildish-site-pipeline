---
title: Architecture and Design
description: "This section explains the overall system shape, design rationale, model fit, and example-driven architecture guidance."
weight: 20
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

Use this section when you need to understand why Site Pipeline has its current
boundaries, models, and execution shape. If you are trying to build your first
site, start with [Getting Started](../getting-started/) instead.

## Start with the system boundary

- [Architecture overview](architecture-overview/) explains the pipeline's
  responsibilities, staged contract, and downstream consumers.
- [Provider end-to-end example](provider-e2e-example/) follows optional provider
  data from authored policy to staged metadata.

## Follow execution and source materialization

- [Build architecture](build-architecture/) covers build and watch execution,
  work ownership, and publication of a completed stage.
- [Source resolution and materialization](source-resolution-and-materialization/)
  separates publication selection from obtaining local source trees.

## Review the model and its rationale

- [Design review](design-review/) records design choices, boundaries, and open
  trade-offs.
- [Model-fit cross-check](model-fit-cross-check/) tests the model against sites
  of different shapes and explains the size bands used in Getting Started.

For exact types, schemas, and validation rules, use the [unreleased development
reference](../development/reference/). Those contracts have not yet been
published as release documentation.
