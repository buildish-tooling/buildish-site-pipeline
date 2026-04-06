---
title: Deferred maintenance follow-ups
description: "This page records small but important follow-up work that is intentionally deferred while nearby changes are being implemented in smaller safe slices."
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

## Raising the production quality bar

The repo-wide audit ended with the implementation in a good state overall, but a
few higher-level refactoring themes still stand out for maintainers who want to
push the codebase from "strong" toward "very strong" or better.

 See [raising-the-production-quality-bar.md](../../../maintenance/raising-the-production-quality-bar/)
for the short maintainer checklist. The highest-leverage themes are thinner
orchestration, more explicit invariants in types, and more aggressively
single-sourced trust-boundary and policy rules.

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

## Optional staged-tree link checking for renderer-specific relative links

Some authored Markdown links are valid as repository-relative source references
but do not survive unchanged once a downstream renderer maps source files to
pretty output URLs.

One concrete example is a source link such as `../foo/bar.md`. That may look
reasonable while editing in the repository tree, but a renderer such as Hugo may
publish the target as a directory-style URL like `../../foo/bar/` instead. In
that shape, a literal carry-through of the authored Markdown link is wrong even
though the intent was clear.

The deferred follow-up is to decide whether site-pipeline should support
optional automatic link diagnostics for staged content and, if so, where the
policy belongs.

Current design direction:

- link checking likely belongs in scope because broken staged links are a real
  publication-quality problem
- blind generic link rewriting in the core pipeline likely does not, because
  link semantics depend on renderer behavior, URL shape policy, and site-local
  conventions that site-pipeline does not fully own
- if the project grows first-class support here, it should be implemented as a
  real supported feature with shared page inventory or equivalent shared page
  facts, not as two unrelated page-tree scans that happen to stay in sync
- the first production slice should support only the clearly modeled URL-shape
  categories `directory` and `file-html`
- `route-mapped` should stay deferred until the project has a concrete,
  testable contract for custom permalink systems instead of a hand-wavy escape
  hatch
- any consumer-owned rule set should be explicit about renderer assumptions and
  should not silently rewrite links unless the contract is narrow, testable, and
  unambiguous
- a future site-pipeline-native link syntax may be worth exploring if authors
  need a way to express page identity or intent without hand-encoding the final
  renderer-shaped URL, but that would add a pipeline-owned authoring surface and
  should therefore stay a later design topic rather than part of the first link
  checking implementation
- broken internal links should still be reported individually rather than hidden
  behind arbitrary per-page, per-component, or global quotas; if report volume
  becomes a real problem, the better answer is reporting compaction or an
  overflow summary diagnostic, not a correctness threshold

Implementation follow-up worth evaluating before this grows further:

- the current page inventory keeps `InventoryPage.body_text`, which means the
  aggregator can retain full authored page bodies in memory longer than link
  checking actually needs them
- a leaner design may be to extract `LinkDescription`-style facts eagerly
  (`target`, `line`, `column`, plus any other minimal routing context), validate
  links as soon as the relevant local route facts are available, and retain only
  the unresolved cross-component links for the final aggregation pass
- that would likely reduce steady-state memory pressure and make the ownership
  split clearer: component-local validation during or after each component pass,
  cross-component validation only in the main aggregator once the full staged
  route inventory exists
- any such refactor must keep diagnostics stable and precise; losing source
  location fidelity or deferring too little information would not be acceptable

Questions worth answering before implementation:

- should the catalog expose this as a general `linkChecks` capability rather
  than a more implementation-leaking `stagedLinkChecks` name
- should site-pipeline only report suspicious links, or also support an
  explicit transformation mode
- how would such rules interact with pretty URLs, index pages, page bundles,
  aliases, mounted content, and non-Hugo renderers
- can the pipeline validate links against the staged output tree without making
  incorrect assumptions about renderer-only features such as shortcodes or
  `ref`/`relref`-style link expansion
- is a pipeline-native link syntax worth the portability cost if it lets
  site-pipeline emit the correct renderer-facing link shape automatically

This should be treated as optional publish-quality assistance for consumers, not
as a reason to make the shared authored contract renderer-specific by default.
