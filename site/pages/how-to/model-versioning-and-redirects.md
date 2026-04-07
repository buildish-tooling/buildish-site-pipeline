---
title: Model versioning and redirects
description: "Use this guide when one product starts needing latest-release, development, archive, or release-specific routes without changing public permalinks by hand."
weight: 18
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

## Start with public URL policy

Decide which public route families the site should preserve, for example:

- latest-release routes
- development routes
- exact release routes
- archive or withdrawn release routes

The important rule is that public routing is consumer-owned policy. It should
not be inferred accidentally from repository names or source layout.

## Let the pipeline resolve routes and redirects

Model canonical routes, aliases, and redirects in the publication layer and then
let the pipeline emit the resolved results in staged metadata.

That gives downstream tooling one coherent view of:

- which routes are canonical
- which routes are aliases
- which requests should redirect

## Verify the result in staged metadata

After a build, inspect:

- the route inventory referenced by `manifest.dataFiles.routes`
- the redirect inventory referenced by `manifest.dataFiles.redirects`

If a deployment target needs concrete server rules, generate them from the
resolved redirect inventory rather than rebuilding redirect behavior from scratch.

## Read this next

- [inspect-staged-output-and-routes.md](../inspect-staged-output-and-routes/)
- [http-server-config-how-to.md](../http-server-config-how-to/)
- [flexible component publication](/components/site-pipeline/development/reference/flexible-component-publication/)
- [security and trust model](/components/site-pipeline/development/reference/security-and-trust-model/)
