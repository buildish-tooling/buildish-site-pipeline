---
title: Jekyll integration status
description: "Current compatibility status and verification requirements for a future Site Pipeline to Jekyll integration guide."
weight: 39
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

## Current status

This repository does not currently contain a Jekyll integration fixture or an
executable synchronization adapter. The integration has not been verified
locally, so this page does not provide a turnkey recipe or claim that mounting
the stage directly is sufficient.

The stable part is the Site Pipeline side of the boundary: a completed
`site/.stage/manifest.json` describes staged content, static files, and aggregate
JSON data. A future Jekyll adapter should consume that contract without
reconstructing routes or version selection from source repositories.

## What must be verified

Before this page becomes an integration guide, a checked-in fixture needs to
prove:

1. how staged Markdown maps into Jekyll collections or the configured source
   tree without changing public routes
2. whether nested `pipeline` front matter remains accessible to Liquid layouts
3. how staged aggregate JSON maps into `_data` without copying `manifest.json`
   into renderer-facing data
4. how staged static files map into the generated site without collisions
5. how `_index.md`-style inputs and pretty routes need to be adapted
6. how a completed stage is synchronized atomically for local and CI builds
7. how redirects remain a deployment-adapter concern rather than an implicit
   Jekyll behavior

## Acceptance criteria for a real guide

A future guide should include:

- a minimal pinned Jekyll project
- a checked-in stage-to-Jekyll adapter or an evidence-backed direct mapping
- one build based on a real Site Pipeline stage
- assertions for page front matter, aggregate data, static assets, and routes
- collision, stale-output, missing-manifest, and malformed-input tests
- copyable local preview and production build commands

Until those checks exist, use this page only as a compatibility-status record.

## Verified alternatives

The repository currently has documented and tested integration paths for
[Hugo](../integrate-with-hugo/) and [Roq](../integrate-with-roq/).

## Read this next

- [Inspect staged output and routes](../inspect-staged-output-and-routes/)
- [Staged output and consumers](../../concepts/staged-output-and-consumers/)
- [Create a tiny site](../create-a-tiny-site/)

For unreleased development contract details:

- [Staged output contract](../../development/reference/staged-output-contract/)
- [Pipeline model schema reference](../../development/reference/pipeline-model-schema-reference/)
