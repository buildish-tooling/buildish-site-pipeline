---
title: Model versioning and redirects
description: "Use this guide when one product starts needing latest-release, development, archive, or release-specific routes without changing public permalinks by hand."
weight: 18
---

<!--
Copyright 2026 The Buildish Authors

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

## Select version contexts explicitly

An artifact combines source-control discovery rules, authored lifecycle data,
and publication selection. This example publishes development docs, every
authored maintenance-line head, and the latest release in each line:

```yaml
artifacts:
  - key: runtime
    source: runtime
    versioning:
      developmentRef: main
      tagPattern: ^v.*$
    publicationSelection:
      development: true
      lineHeads:
        mode: allAuthored
      releases:
        mode: latestPerLine
    lifecycle:
      releaseLines:
        - key: "4.0"
          maintenanceRef: maintenance/4.0
          latest: "4.0.0"
      releases:
        - version: "4.0.0"
```

The matching provider snapshot records supply the resolved `main`,
`maintenance/4.0`, and `v4.0.0` contexts. The authored catalog still owns which
of those contexts are published and where they appear.

## Distinguish routes, aliases, and redirects

- A published or context route identifies content that exists at a public path.
- An alias is another public route for the same target.
- A redirect tells the deployment layer to send one request URL to another
  resolved target.

For example, add a redirect when an old development-docs entry point should now
lead to the exact release:

```yaml
publication:
  mountPath: /spark/
  redirects:
    - fromPath: /spark/development/docs/
      target: release:spark/runtime@4.0.0
      status: 308
      reason: Current docs live on the latest release route.
```

Typed targets such as `release:spark/runtime@4.0.0` keep the destination tied to
the resolved publication model. Use `route:/path/` when the public route itself
is the intended target, or a fully qualified URL for an external destination.

Allowed redirect statuses are `301`, `302`, `307`, and `308`. Choose the status
as part of publication policy; downstream adapters should preserve it.

## Build and inspect the resolved result

```bash
site-pipeline check
site-pipeline build
```

The route aggregate should contain the selected contexts:

```text
/spark/development/
/spark/development/4.0/
/spark/releases/4.0.0/
```

The redirect aggregate should contain a resolved entry like this:

```json
{
  "fromUrl": "https://docs.example.org/spark/development/docs/",
  "toUrl": "https://docs.example.org/spark/releases/4.0.0/",
  "status": 308,
  "reason": "Current docs live on the latest release route.",
  "sourceKind": "catalog"
}
```

Use `routes.json` to understand route ownership and canonical/alias state. Use
`redirects.json` to generate concrete server or edge behavior.

## Failure cases to resolve before deployment

- A typed target must refer to a selected component, artifact, line, release, or
  route.
- `fromPath` must belong to the declared origin and must not conflict with
  published content.
- Alias and canonical paths must resolve without ambiguous ownership.
- Provider records must agree with the authored version, tag, ref, and
  publication state.
- A deployment adapter must not rebuild or reinterpret redirect destinations
  from request-derived host values.

## Read this next

- [Inspect staged output and routes](../inspect-staged-output-and-routes/)
- [Create HTTP server configuration](../http-server-config-how-to/)

For unreleased development contract details:

- [flexible component publication](../../development/reference/flexible-component-publication/)
- [security and trust model](../../development/reference/security-and-trust-model/)
