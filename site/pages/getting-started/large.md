---
title: Large sites
weight: 14
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

This page is for platform-style sites with many modules, sibling projects, or
extensions that share publication policy but still need explicit routing,
lifecycle, and compatibility behavior.

## Who this is for

- one platform plus many modules or sibling projects
- several active release lines
- grouped publication policy and compatibility rules matter

## Smallest useful mental model

At this size, the site is an ecosystem rather than a single product. The key
shift is to treat publication defaults, route ownership, compatibility metadata,
and provider enrichment as first-class modeled inputs.

## Read these first

1. [../how-to/organize-grouped-components-and-publication-policy.md](../how-to/organize-grouped-components-and-publication-policy.md)
2. [../how-to/plan-publication-and-materialization.md](../how-to/plan-publication-and-materialization.md)
3. [../how-to/integrate-provider-compatibility-and-translation-data.md](../how-to/integrate-provider-compatibility-and-translation-data.md)

## Usually still background material

Only skip localization and provider topics if the site truly does not need them.
For many large sites, those topics are already close to the critical path.

## Read this next when you grow

Move to [very-large.md](very-large.md) when the site spans many repositories or
product families and needs stronger operational boundaries, localization policy,
or very large redirect inventories.

## Deeper reference trail

- [flexible component publication](/docs/reference/flexible-component-publication/)
- [provider snapshot schema](/docs/reference/provider-snapshot-schema/)
- [provider to staged metadata mapping](/docs/reference/provider-to-staged-metadata-mapping/)
- [security and trust model](/docs/reference/security-and-trust-model/)