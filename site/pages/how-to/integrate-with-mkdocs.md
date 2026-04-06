---
title: How to integrate Site Pipeline with MkDocs
description: "This page is a stub for the future MkDocs integration guide."
weight: 40
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

## What this guide will cover

- how to feed staged content into an MkDocs-based site
- how to work with MkDocs navigation and plugin expectations without moving
  publication logic out of Site Pipeline
- how to combine staged output updates with MkDocs local preview workflows
- how to use staged JSON metadata for search, nav, or custom plugin inputs

## Why this guide matters

MkDocs is a common choice for docs teams that want a Python-friendly renderer.
A dedicated guide should explain how to keep MkDocs focused on rendering while
Site Pipeline continues to own publication paths, version context, and staged
metadata.

## Planned guide shape

1. explain the staged-output contract MkDocs should read
2. show a minimal MkDocs project layout
3. show a local development workflow with staged inputs and MkDocs preview
4. explain how to bridge staged metadata into MkDocs config or plugins
5. note MkDocs-specific integration caveats

## Read this next

- [inspect staged output and routes](../inspect-staged-output-and-routes/)
- [../concepts/staged-output-and-consumers.md](../../concepts/staged-output-and-consumers/)
- [staged output contract](/components/site-pipeline/development/reference/staged-output-contract/)
