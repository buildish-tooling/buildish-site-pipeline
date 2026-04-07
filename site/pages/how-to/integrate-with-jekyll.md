---
title: How to integrate Site Pipeline with Jekyll
description: "This page is a stub for the future Jekyll integration guide."
weight: 39
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

- how to treat `site/.stage/` as the Site Pipeline to Jekyll hand-off boundary
- how to connect staged Markdown, front matter, static files, and JSON data to a
  Jekyll site
- how to preserve a clean local loop while editing versioned docs
- how to avoid making Jekyll reconstruct routing or version logic from source
  repositories

## Why this guide matters

Some consumers already have Jekyll-based sites or want a renderer that works
well with front matter driven content. A dedicated guide should show how Jekyll
fits without changing the Site Pipeline contract.

## Planned guide shape

1. explain the staged-output contract Jekyll should consume
2. show a minimal Jekyll project layout
3. show a local development workflow around staged inputs
4. explain where version paths, redirects, and metadata should come from
5. note Jekyll-specific integration caveats

## Read this next

- [inspect staged output and routes](inspect-staged-output-and-routes/)
- [../concepts/staged-output-and-consumers.md](../concepts/staged-output-and-consumers/)
- [staged output contract](/components/site-pipeline/development/reference/staged-output-contract/)
