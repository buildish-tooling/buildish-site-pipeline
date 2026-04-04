---
title: Create a tiny site
weight: 16
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

Use this guide when you want the smallest useful Site Pipeline setup: one
consumer-owned site catalog, one component, and one staged output.

## Recommended shape

Start with:

- one `site/components.yaml` file in the consumer repository
- one participating component repository
- one `site/component.yaml` file in that component repository
- one main authored docs tree and optional site-owned pages or assets

The README's minimal flow is the right starting point:

1. create the component catalog in `site/components.yaml`
2. provide per-component `site/component.yaml`, `site/pages/`, `site/docs/`,
   and optional `site/assets/` inputs
3. keep local machine remapping in `site/components.local.yaml` only
4. run `site-pipeline build --repo-root <consumer-repo>`
5. point the downstream renderer at `site/.stage/`

## What to decide early

Even for a tiny site, decide these explicitly:

- the stable component identity
- which content roots belong to the component repository
- which content belongs to the consumer-owned site layer instead

That keeps component identity separate from future publication layout changes.

## What success looks like

You are in a good starting state when:

- the pipeline produces one coherent stage root
- `manifest.json` is present and readable
- staged pages and assets are separated from source layout details
- a renderer can consume the stage root without reading repositories directly

## Read this next

- [inspect-staged-output-and-routes.md](inspect-staged-output-and-routes.md)
- [../reference/flexible-component-publication.md](../reference/flexible-component-publication.md)
- [../reference/staged-output-contract.md](../reference/staged-output-contract.md)