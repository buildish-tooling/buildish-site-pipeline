---
title: Scale Site Pipeline operations
description: "Use this guide when the site has enough sources, redirects, lifecycle data, or deployment targets that operational boundaries become part of the design."
weight: 22
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

## Focus on boundaries first

At large scale, the main operational concerns are usually:

- planning scope versus staged output scope
- materialization strategy and cache behavior
- trust boundaries for provider, localized, or mounted content
- large route and redirect inventories

Scale the operating process around those boundaries rather than making one
renderer or checkout script responsible for the whole publication model.

## Use the same gated runbook in local and CI workflows

### 1. Inventory selected inputs

```bash
site-pipeline plan --for build \
  --report-format json \
  --report-schema-version 1 \
  --report-output materialization-report.json
```

Track counts and statuses by `inputKind`, source, component, and artifact. A
sudden increase usually means publication selection changed and should be
reviewed before acquisition or staging.

### 2. Materialize with consumer-owned tooling

Fetch or refresh only the inputs in the planning report. Keep credentials,
network retries, cache eviction, and source-control operations in that layer.
Rerun planning after acquisition so the next gate uses current evidence.

### 3. Validate the complete local workspace

```bash
site-pipeline check \
  --report-format json \
  --report-schema-version 1 \
  --report-output check-report.json
```

Gate on the report summary and retain diagnostics as build evidence. Do not
publish when route ownership, references, translation linkage, provider data,
or path safety fails validation.

### 4. Build one completed stage

```bash
site-pipeline build
```

Publish or render only after `manifest.json` exists in the completed stage. A
consumer should keep the prior completed publication available if a later run
fails.

### 5. Adapt for each deployment target

Give each renderer or deployment adapter the stage root and the origins it owns.
Adapters should discover aggregate paths through the manifest and reject entries
outside their target hosts or origins.

## Monitor the inventories that drive cost

Measure trends in:

- selected version contexts and materialized source trees
- staged page and asset counts
- route, redirect, translation, and compatibility entries
- plan, check, staging, rendering, and adapter duration
- warning/error counts by stable diagnostic code

Use observed inventories to set consumer-side timeouts, job partitioning, and
retention policies. Keep the pipeline's validation limits intact; weakening
them to accommodate one unusually large input hides an ownership or partitioning
problem.

## Define a failure playbook

| Signal | Owner | Response |
| --- | --- | --- |
| plan reports missing or stale input | acquisition layer | fetch or refresh the named local input, then plan again |
| check reports invalid authored/provider data | source or catalog owner | correct the input; do not stage |
| route or translation collision | publication-policy owner | resolve ownership or linkage; do not guess in the renderer |
| build fails before a completed manifest | pipeline operator | retain the previous completed stage and investigate diagnostics |
| adapter sees an unknown origin | deployment owner | reject or isolate the entry instead of stripping the host |

## Recommended operating posture

1. keep the staged contract authoritative for downstream consumers
2. keep materialization strategy replaceable and separate from publication policy
3. fail closed on malformed route, redirect, or provider data
4. size operational limits around real inventories rather than assuming tiny
   sites forever
5. keep deployment adapters and server config generation downstream of the stage

## When to partition work

Partition by a real publication or deployment boundary, such as independently
owned origins or separately deployed product families. Preserve a coherent
route-ownership check across partitions. Repository count alone is not a safe
partition key because several repositories may contribute to one public route
family.

## Read this next

- [Plan publication and materialization](../plan-publication-and-materialization/)
- [Create HTTP server configuration](../http-server-config-how-to/)

For unreleased development contract details:

- [security and trust model](../../development/reference/security-and-trust-model/)
- [Source resolution and materialization](../../architecture/source-resolution-and-materialization/)
