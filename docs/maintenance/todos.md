---
title: Deferred maintenance follow-ups
description: "This page records small but important follow-up work that is intentionally deferred while nearby changes are being implemented in smaller safe slices."
weight: 35
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

## CI changed-files gating after previous failures

The current CI changed-files detection compares the current head only against the
event base SHA. That is fine for the common fast path, but it can skip important
jobs when an earlier commit in the same push or pull request already failed a
gated job and the newest commit does not touch one of the trigger paths.

The deferred follow-up is to make the changed-files gating logic aware of prior
failed jobs for the same branch or pull request, so a follow-up commit does not
incorrectly skip `check` just because the newest diff is narrower.

Any future fix should preserve the current optimization goal while making the
failure recovery path safe and predictable.

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

## Follow-ups for unstable watch readiness events

The first slice of explicit watch readiness signaling now exists:

- `site-pipeline watch --unstable-events jsonl [--unstable-events-output PATH|-]`
- machine-readable events `ready`, `cycle-succeeded`, and `cycle-failed`
- human-facing `--verbose` and `--debug` output routed to `stderr`
- documentation for the event-sink contract plus defensive malformed-line
  handling in the API contract

The remaining work in this area is follow-up hardening and ergonomics, not the
basic event-stream introduction. Follow-ups worth evaluating include:

- whether the publication path should explicitly `fsync` the final manifest file
  and/or parent directory before declaring a new trusted stage ready
- whether a simpler shell-oriented `--ready-file <path>` mechanism is still
  worth offering later despite weaker cross-filesystem semantics than stdio
- whether downstream renderers such as Hugo still need extra startup-burst
  mitigation even when wrappers wait for the explicit `ready` event

This work should improve operator ergonomics without changing the current safety
rules around trusted-stage publication or weakening the manifest-last contract.

## Future watch-report ergonomics for long-running sessions

`plan`, `build`, and `check` can emit a full text report because they are
finite snapshot-style commands. `watch` is different: replaying the full warning
or error list on every cycle would quickly become noisy once a workspace has a
large steady-state diagnostic set.

The deferred follow-up here is not "print full text reports every cycle". It is
to decide whether `watch` should grow a more explicit reporting contract for
long-running sessions.

If this grows, the design should likely keep the current boundary:

- lifecycle logging stays concise and summary-oriented per cycle
- a report sink may still hold the latest full snapshot when explicitly
  requested
- any terminal-facing detailed output should prefer changed or newly introduced
  diagnostics over replaying the entire unchanged set every cycle
- delta or incremental reporting should be treated as a separate explicit
  feature with a testable contract, not as an accidental side effect of the
  current snapshot report path

This should be treated as operator-ergonomics work, not as a reason to make the
default `watch` terminal output much noisier.

## Optional staged-tree link checking for renderer-specific relative links

This is no longer purely deferred work. Site Pipeline now has a narrow but real
first slice of optional internal page-link checking.

The current shipped shape is:

- consumers can opt in through `validation.linkChecks` in `site/catalog.yaml`
- `check` validates authored internal page links against the resolved staged
  public routes
- the policy is explicit about URL-shape assumptions via `mode`, currently only
  `directory` and `file-html`
- root-absolute links can also be checked when `checkRootAbsolute` is enabled
  and `internalPrefixes` declares which public-path prefixes are truly internal
- findings are reported as individual warnings such as
  `page-link-target-missing`
- the implementation intentionally validates only; it does not rewrite authored
  links

That means the original question of whether this belongs in the catalog is now
answered: yes, but only as a small consumer-owned validation policy rather than
as a renderer-specific rewriting system.

What is still intentionally limited:

- the feature only covers clearly modeled URL-resolution modes `directory` and
  `file-html`
- renderer-owned expansion mechanisms such as Hugo `ref`/`relref`, shortcodes,
  or other custom permalink systems are still out of scope
- generic link rewriting is still out of scope because the pipeline does not own
  renderer semantics tightly enough to do that safely
- the diagnostics focus on internal page targets; they are not a full general
  web-link or asset-link checker

Remaining follow-up worth evaluating if this grows further:

- whether component-local link facts can be validated earlier, with only the
  unresolved cross-component cases carried into the final aggregation pass
- whether future route modes beyond `directory` and `file-html` can be added as
  real tested contracts instead of vague renderer-specific escape hatches
- whether better compaction is needed if warning volume ever becomes noisy;
  broken internal links should still be reported individually rather than hidden
  behind arbitrary quotas

For now, this should still be treated as optional publish-quality assistance for
consumers, not as a reason to make the shared authored contract renderer-
specific by default.
