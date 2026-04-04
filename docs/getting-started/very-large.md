---
title: Very-large sites
weight: 15
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

This page is for publication systems that span many repositories, multiple
product families, and strong permalink, trust-boundary, and localization needs.

## Who this is for

- many repositories or doc sources
- multiple product families under one staged contract
- localization, mounted content, and generated refs may all be in play

## Smallest useful mental model

At this size, the pipeline is a normalization boundary between authored policy,
provider-derived lifecycle data, localized content, and deployment-specific
outputs. The public staged contract matters more than any single source layout.

## Read these first

1. [../how-to/integrate-provider-compatibility-and-translation-data.md](../how-to/integrate-provider-compatibility-and-translation-data.md)
2. [../how-to/scale-site-pipeline-operations.md](../how-to/scale-site-pipeline-operations.md)
3. [../how-to/http-server-config-how-to.md](../how-to/http-server-config-how-to.md)

## What you should treat as first-class concerns

- route ownership and long-lived permalink stability
- trust boundaries between authored inputs, provider data, and deployment config
- translation linkage and mounted/generated content boundaries
- operational controls for planning, caches, and large inventories

## Read next

At this size, the next step is usually not another size band. It is a deeper
reference pass through the contracts and security model.

## Deeper reference trail

- [../v1/architecture-overview.md](../v1/architecture-overview.md)
- [../v1/staged-output-contract.md](../v1/staged-output-contract.md)
- [../v1/security-and-trust-model.md](../v1/security-and-trust-model.md)
- [../v1/pipeline-model-schema-reference.md](../v1/pipeline-model-schema-reference.md)