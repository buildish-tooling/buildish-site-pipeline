---
weight: 35
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

# Consumer workspace and CI model

This document explains how a consumer repository binds component slugs to local
checkouts, stages partial workspaces safely, and keeps CI inputs reproducible.

## Current workspace model

Today the shared catalog identifies each component with a `slug` plus a
consumer-managed checkout hint such as `localDir`.

With `--repo-root <consumer-repo>`, the current contract resolves:

- consumer-owned paths such as `site/components.yaml` relative to the repo root,
- catalog `localDir` values relative to the workspace parent, and
- optional `site/components.local.yaml` overrides relative to the consumer repo
  root.

Missing component checkouts are ignored cleanly rather than treated as errors or
collapsed into unrelated parent watch roots.

## Keep identity separate from workspace bindings

Even when the current catalog uses `localDir`, the important design principle is
that component identity should stay stable while checkout bindings remain
workspace-local.

In practice that means:

- the shared catalog owns public component identity and default content roots,
- `site/components.local.yaml` should only redirect a slug to a different local
  checkout, and
- local overrides must not redefine published metadata such as slugs,
  repository identity, or lifecycle labels.

## Resolution precedence

Source resolution should remain conservative:

1. CI-provided resolved inputs, when a workflow materializes them explicitly
2. local checkout overrides from `site/components.local.yaml`
3. committed catalog checkout hints and conventional sibling discovery
4. missing checkout -> skip the component cleanly

Content-structure precedence remains separate:

1. per-component catalog overrides
2. component metadata in `site/component.yaml`
3. catalog defaults
4. built-in defaults

## Partial workspaces are normal

Consumers should be able to clone only the repositories they need for one task.
A local build may therefore stage only a subset of the published component
inventory.

That is why the pipeline treats missing component checkouts as a normal local
state rather than a failure.

## CI guidance

CI should resolve moving references early and then build from fixed inputs.

A good model is to record, for each staged source:

- component slug,
- repository identity,
- content kind such as `development` or `release`,
- resolved commit SHA, and
- checkout or snapshot path used for the build.

The rest of the workflow should then consume only those resolved inputs.

## Scaling release inputs

The expensive case is historical release content, not development checkouts.
Consumers should therefore prefer incremental release snapshots or equivalent
immutable release artifacts over re-materializing every historical tag on every
build.

## Read next

- [Site component contract](../site-component-contract/)
- [Design principles and future evolution](../design-principles/)
- [Adoption guide](../adoption-guide/)
