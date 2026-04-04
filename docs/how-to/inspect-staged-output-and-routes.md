---
title: Inspect staged output and routes
weight: 17
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

Use this guide after a successful build when you want to understand what the
pipeline actually staged and which public routes it resolved.

## Start with the manifest

Always read `manifest.json` first.

It is the authoritative entry point for:

- the top-level staged roots
- which aggregate data files are present
- where the route and redirect inventories live for this stage

## Then inspect the route surfaces

The most useful next files are usually:

- the path referenced by `manifest.dataFiles.routes`
- the path referenced by `manifest.dataFiles.redirects`

Use them to answer different questions:

- `routes.json` tells you which public routes the stage owns
- `redirects.json` tells you which requests should redirect and where they go

## Keep the contract boundary in mind

The staged tree is the downstream contract. Renderers, deployment adapters, and
audit tools should integrate against the stage root instead of reading internal
Python objects or arbitrary source repositories.

## Typical next steps

- generate HTTP-server or CDN config from the route and redirect metadata
- validate that the expected latest, archive, or alias routes exist
- inspect page front matter under the staged content tree

## Read this next

- [http-server-config-how-to.md](http-server-config-how-to.md)
- [../v1/staged-output-contract.md](../v1/staged-output-contract.md)
- [../v1/pipeline-model-schema-reference.md](../v1/pipeline-model-schema-reference.md)