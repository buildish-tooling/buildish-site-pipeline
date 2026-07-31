---
title: Plan publication and materialization
description: "Use this guide when the site has enough versions, refs, or imported inputs that you need an explicit planning step before staging starts."
weight: 19
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

## Keep three concerns separate

The model separates:

1. version selection
2. source materialization
3. staging

That separation matters because a cache branch, snapshot store, or generated
local tree is a materialization strategy, not a publication concept.

## Request a machine-readable build plan

For automation, request the report schema explicitly:

```bash
site-pipeline plan --for build --report-format json --report-schema-version 1
```

An abridged report entry looks like this:

```json
{
  "schemaVersion": 1,
  "target": "build",
  "entries": [
    {
      "sourceKey": "runtime",
      "inputKind": "released",
      "componentSlug": "spark",
      "artifactKey": "runtime",
      "version": "4.0.0",
      "tag": "v4.0.0",
      "expectedLocalPath": "/workspace/components/runtime/docs/releases/4.0.0",
      "status": "present",
      "provenance": "snapshot",
      "watchEligible": false
    }
  ],
  "diagnostics": []
}
```

`expectedLocalPath` is a local filesystem path, not a public URL or staged
route. A report can complete successfully while entries are `missing`, `stale`,
or `unresolved`; those states tell the consumer what acquisition work remains.

Use `--for watch` when the consumer needs watch eligibility and watch-scoped
input requirements. Write the report to a file with `--report-output` when a
wrapper needs to consume it after the command exits.

## Materialize outside the pipeline

For every entry that is not ready:

1. Resolve the source key, ref, tag, or version with consumer-owned SCM or cache
   tooling.
2. Populate the exact local path described by the report.
3. Rerun `plan` until the inventory reflects the expected state.

Site Pipeline deliberately does not fetch repositories, update cache branches,
or choose a snapshot-store implementation. That keeps acquisition credentials
and network behavior outside the staging process.

## Validate and stage

Once the selected local inputs exist:

```bash
site-pipeline check
site-pipeline build
```

For a long-running local renderer loop, use `watch` only after a watch plan says
the relevant inputs are watch-eligible.

## Complete workflow

1. decide which publication contexts should exist for the target build or watch
   cycle
2. use the planning step to resolve which local inputs are required
   - these can include top-level site pages, top-level site assets, top-level
     vendor asset roots, and the selected component docs trees
3. materialize those inputs using the consumer's chosen strategy
4. run `check` to validate the resolved inputs and authored metadata
5. run `build` or `watch` once the local trees are ready

## Failure and recovery behavior

- Invalid invocation or a JSON report without an explicit schema version fails
  before planning.
- Missing or stale inputs remain report data; the consumer decides whether and
  how to acquire them.
- Error diagnostics that prevent a usable plan return a domain failure.
- `check` can still find invalid content, links, references, or routes after all
  inputs are present.
- Acquisition should be repeatable: rerunning it for an already-correct input
  should not change publication policy or staged paths.

This separation makes it possible to replace an SCM checkout strategy with a
cache or snapshot store without changing the catalog or downstream stage.

## Read this next

- [Source resolution and materialization](../../architecture/source-resolution-and-materialization/)

For unreleased development contract details:

- [validation and check](../../development/reference/validation-and-check/)
- [API contract](../../development/reference/api-contract/)
