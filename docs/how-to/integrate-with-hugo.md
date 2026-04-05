---
title: How to integrate Site Pipeline with Hugo
weight: 38
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

# How to integrate Site Pipeline with Hugo

This page is a stub for the future Hugo integration guide.

## What this guide will cover

- how to point Hugo at `site/.stage/`
- how to combine `site-pipeline watch` with `hugo serve`
- how to map staged pages, static assets, and JSON data into a Hugo site
- how to use `manifest.json` for stage discovery without pulling it into normal
  Hugo template data
- how to keep renderer responsibilities separate from Site Pipeline

## Why this guide matters

Hugo is the main renderer example used across the current user-facing docs. A
full guide should make it obvious that Site Pipeline prepares the staged site,
while Hugo renders and serves it.

That guide should also make it clear that `manifest.json` is a discovery and
publication-marker file. Hugo should normally render from staged pages and
aggregate JSON data, not from the manifest itself.

## Planned guide shape

1. explain the hand-off from `site/.stage/` to Hugo
2. show a minimal Hugo project layout
3. show a local development workflow with `site-pipeline watch` and
   `hugo serve`
4. explain how to read staged front matter and aggregate JSON data safely
5. show deployment-oriented build hand-off points

## Read this next

- [inspect staged output and routes](inspect-staged-output-and-routes.md)
- [../concepts/staged-output-and-consumers.md](../concepts/staged-output-and-consumers.md)
- [../reference/staged-output-contract.md](../reference/staged-output-contract.md)