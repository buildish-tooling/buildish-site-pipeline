---
title: MkDocs integration status
description: "Current compatibility status and verification requirements for a future Site Pipeline to MkDocs integration guide."
weight: 40
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

This repository does not currently contain an MkDocs integration fixture or an
executable synchronization adapter. The integration has not been verified
locally, so this page does not provide a turnkey recipe or claim that assigning
the staged content root to `docs_dir` preserves the complete contract.

The stable part is the Site Pipeline side of the boundary: a completed
`site/.stage/manifest.json` describes staged content, static files, and aggregate
JSON data. A future MkDocs adapter should consume that contract while leaving
route ownership, lifecycle selection, and redirect resolution in Site Pipeline.

## What must be verified

Before this page becomes an integration guide, a checked-in fixture needs to
prove:

1. how staged content maps into `docs_dir` without flattening component,
   version, or locale routes
2. how MkDocs navigation is generated or configured from staged metadata
3. whether nested `pipeline` front matter is available to the selected theme
   and plugin layer
4. how aggregate JSON becomes renderer data without exposing `manifest.json` as
   ordinary template data
5. how staged static assets are copied and collision-checked
6. whether `_index.md` and other directory-index conventions require adaptation
7. how local preview observes only completed stage updates
8. how redirects remain a deployment-adapter concern

## Acceptance criteria for a real guide

A future guide should include:

- a minimal pinned MkDocs project and explicit plugin set
- a checked-in stage-to-MkDocs adapter or an evidence-backed direct mapping
- one build based on a real Site Pipeline stage
- assertions for navigation, page metadata, aggregate data, assets, and routes
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
