---
title: Integrate provider, compatibility, and translation data
weight: 21
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

Use this guide when authored publication policy is no longer enough by itself and
the site needs provider-derived lifecycle data, compatibility metadata, or
translation linkage.

## Keep ownership boundaries explicit

The clean split is:

- authored site and catalog metadata own public policy and route intent
- provider snapshots enrich lifecycle and release-state information
- compatibility metadata expresses cross-component or cross-artifact support
- translation linkage relates localized pages without redefining route policy

## Recommended workflow

1. define the authored publication model first
2. add provider snapshots as enrichment, not as route ownership
3. map provider data into staged aggregates intentionally
4. model compatibility relationships explicitly instead of inferring them from
   exact version strings alone
5. validate translation linkage and locale data separately from provider input

## Safety rule

Provider input must not silently redefine public URLs, artifact identity, or
consumer-owned publication policy.

## Read this next

- [../v1/provider-snapshot-schema.md](../v1/provider-snapshot-schema.md)
- [../v1/provider-to-staged-metadata-mapping.md](../v1/provider-to-staged-metadata-mapping.md)
- [../v1/security-and-trust-model.md](../v1/security-and-trust-model.md)
- [../v1/pipeline-model-schema-reference.md](../v1/pipeline-model-schema-reference.md)