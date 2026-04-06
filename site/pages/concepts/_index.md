---
title: Site Pipeline Concepts
weight: 12
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

Use this section when you want the Site Pipeline mental model before diving into
procedures or contracts.

These pages explain what the pipeline owns, what a minimal site looks like, and
how authored inputs become a staged output that renderers and deployment
adapters can consume safely.

## Start here

- [tiny-site-shape.md](tiny-site-shape.md) for the first concrete repository and
  catalog shape
- [staged-output-and-consumers.md](staged-output-and-consumers.md) for the
  manifest, staged front matter, and aggregate-data boundary

## Read next

- [../getting-started/tiny.md](../getting-started/tiny.md) for the smallest
  supported onboarding path
- [../how-to/create-a-tiny-site.md](../how-to/create-a-tiny-site.md) for the
  first copy-pasteable setup
- [staged output contract](/docs/reference/staged-output-contract/)
  for the durable downstream contract