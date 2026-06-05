---
title: Organize grouped components and publication policy
description: "Use this guide when one docs estate starts behaving like an ecosystem with many components, artifacts, or publication surfaces that should share defaults."
weight: 20
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

## What to centralize

Keep these concerns in the consumer-owned catalog layer:

- origins and public base URLs
- group-level defaults
- publication path policy
- per-component or per-artifact publication overrides

That lets component repositories keep owning identity and content roots without
owning the final public URL design.

## Recommended approach

1. define the publication defaults that most components should inherit
2. create groups only when they express a real shared policy or navigation layer
3. override publication shape per component or artifact only when required
4. validate route collisions and ambiguous ownership strictly

## When to add another group

Add a group when it gives a clearer shared default layer. Do not add groups just
to mirror repository layout or organization charts.

## Read this next

- [flexible component publication](../../development/reference/flexible-component-publication/)
- [plan-publication-and-materialization.md](../plan-publication-and-materialization/)
- [pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
