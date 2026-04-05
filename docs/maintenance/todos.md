---
title: Deferred maintenance follow-ups
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

# Deferred maintenance follow-ups

This page records small but important follow-up work that is intentionally
deferred while nearby changes are being implemented in smaller safe slices.

## Local operator path-mapping overrides

The CLI now separates the shared authored catalog path from the operator's
workspace root. That unblocks multi-repository layouts such as CI workspaces
where several repositories are checked out side by side.

Developer machines remain a separate concern. Local clones are often spread
across arbitrary host paths and should not force the shared catalog to carry
machine-specific overrides.

The deferred follow-up is an explicit operator-local override input, likely a
mapping from component slug to local checkout directory. The key properties of
that future feature should stay:

- local-only and typically `.gitignore`'d
- not part of the shared authored catalog contract
- explicit at CLI invocation time rather than silently auto-discovered
- reviewed against watch-mode, diagnostics, and path-trust rules before paths
  outside the declared workspace are accepted

Until that lands, the supported multi-repository shape is:

- a caller-provided `--workspace-root` that contains the intended shared local
  inputs
- a caller-provided `--catalog` that points at the authored site catalog

## Gentler watch updates for downstream renderers

The current incremental watch implementation already narrows worker rebuilds to
the dirty owned units, but coordinator-owned aggregate outputs are still treated
as a conservative shared set.

That means a small page-content edit can still recreate shared JSON outputs such
as `data/components.json`, `data/routes.json`, and other coordinator-owned files
even when their serialized bytes did not change. Downstream renderers such as
`hugo serve` then observe more stage churn than necessary.

The deferred follow-up is a smaller-churn publication path for coordinator-owned
watch outputs. Any implementation must keep the existing safety properties:

- no partial visible-stage updates
- `manifest.json` remains the publication commit point and is written last
- retained trusted stages stay safe on failing watch cycles
- ownership and cleanup rules stay explicit and auditable

The likely design space is one of:

- preserve coordinator-owned files in the seeded candidate stage and rewrite only
  the ones whose serialized bytes actually changed
- or keep the current removal model but compare regenerated coordinator-owned
  outputs against the trusted stage before publication and preserve unchanged
  files without refreshing their mtimes

This should be treated as renderer-gentleness and operational-stability work,
not as a reason to weaken the current publication-integrity rules.