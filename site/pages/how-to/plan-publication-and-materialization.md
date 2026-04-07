---
title: Plan publication and materialization
description: "Use this guide when the site has enough versions, refs, or imported inputs that you need an explicit planning step before staging starts."
weight: 19
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

## Keep three concerns separate

The model separates:

1. version selection
2. source materialization
3. staging

That separation matters because a cache branch, snapshot store, or generated
local tree is a materialization strategy, not a publication concept.

## Recommended workflow

1. decide which publication contexts should exist for the target build or watch
   cycle
2. use the planning step to resolve which local inputs are required
   - these can include top-level site pages, top-level site assets, top-level
     vendor asset roots, and the selected component docs trees
3. materialize those inputs using the consumer's chosen strategy
4. run `check` to validate the resolved inputs and authored metadata
5. run `build` or `watch` once the local trees are ready

## Why this helps

This workflow keeps the contracts clear:

- planning says what inputs are needed
- materialization obtains them
- staging turns them into the stable downstream contract

## Read this next

- [../architecture/source-resolution-and-materialization.md](../architecture/source-resolution-and-materialization/)
- [validation and check](/components/site-pipeline/development/reference/validation-and-check/)
- [api contract](/components/site-pipeline/development/reference/api-contract/)
