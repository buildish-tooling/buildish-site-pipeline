---
title: Scale Site Pipeline operations
description: "Use this guide when the site has enough sources, redirects, lifecycle data, or deployment targets that operational boundaries become part of the design."
weight: 22
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

## Focus on boundaries first

At large scale, the main operational concerns are usually:

- planning scope versus staged output scope
- materialization strategy and cache behavior
- trust boundaries for provider, localized, or mounted content
- large route and redirect inventories

## Recommended operating posture

1. keep the staged contract authoritative for downstream consumers
2. keep materialization strategy replaceable and separate from publication policy
3. fail closed on malformed route, redirect, or provider data
4. size operational limits around real inventories rather than assuming tiny
   sites forever
5. keep deployment adapters and server config generation downstream of the stage

## Read this next

- [plan-publication-and-materialization.md](../plan-publication-and-materialization/)
- [http-server-config-how-to.md](../http-server-config-how-to/)
- [security and trust model](../../development/reference/security-and-trust-model/)
- [../architecture/source-resolution-and-materialization.md](../../architecture/source-resolution-and-materialization/)
