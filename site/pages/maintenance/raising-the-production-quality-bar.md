---
title: Raising the production quality bar
description: "This note is for maintainers who want to move the Site Pipeline codebase from \"strong\" toward \"very strong\" or better. It is not a bug list. It is a maintainer checklist for the next quality step once correctness and coverage are already in good shape."
weight: 36
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

## Current assessment

This codebase is no longer at the earlier "good but still obviously duplicated"
stage. Recent work already landed some of the highest-value cleanup:

- thinner CLI invocation orchestration
- typed artifact identities in reference lookups
- one canonical symlink-ancestry trust helper
- one shared public-path helper reused by planning, staging, and evaluation
- explicit result objects for watch follow-up cycles
- better maintainer-facing docs around shared public-path behavior

That means the remaining gap to an excellent rating is narrower now. It is less
about broad cleanup themes and more about finishing a few specific shape
improvements across production code, tests, and docs.

## What still needs to change in production code

### 1. Thin the remaining heavy coordinators

The biggest production-code gap is not general correctness. It is that a few
important entry points still carry too much orchestration in one place.

The main examples are:

- `src/apache_buildish_site_pipeline/staging/coordinator.py`
- `src/apache_buildish_site_pipeline/planning/__init__.py`
- `src/apache_buildish_site_pipeline/evaluation/execution.py`

These modules are understandable, but they still combine phase ordering,
boundary decisions, result assembly, and failure cleanup closely enough that
future review work will stay heavier than it needs to be.

The excellent-bar target is:

- top-level functions that mostly wire phases together
- phase-local result objects instead of ad hoc handoff shapes
- decision helpers that separate policy from filesystem mutation or report
  assembly

### 2. Finish replacing mixed return shapes with explicit result models

The code is better here than before, but one notable example still stands out:
`planning.build_plan.build_effective_build_plan()` returns
`tuple[PlanToBuildBridge, EffectiveBuildPlan | None]`.

That is still a mixed "status plus optional payload" shape. It works, but it is
exactly the kind of contract that gets misread later.

The excellent-bar target is:

- one named result type per important transition
- no important branch encoded as positional tuple meaning
- constructors that make the allowed states obvious to readers

### 3. Add a few deliberate internal impossibility checks

Edge validation is strong already. The next improvement is to fail louder when
internal layers contradict each other after validation has already succeeded.

The best candidates are the boundaries between:

- planning and build-plan handoff
- publication index and route inventory assembly
- worker results and aggregate-file assembly

These checks should not duplicate user-input validation. They should assert
maintainer-facing invariants that "must already be true here".

### 4. Remove compatibility fossils once they stop protecting a real boundary

One good example is `staging.worker_protocol.WorkerResultWire`, which still keeps
legacy flat counters and a `normalized()` compatibility path next to the newer
`output_stats` shape.

If older worker payloads are no longer a real supported boundary, the excellent
version of the code should remove that compatibility baggage instead of carrying
it forever.

The rule here is simple: keep defensive compatibility code only when it protects
a real, documented boundary that still exists.

## What still needs to change in the test codebase

### 1. Put more weight on scenario tests that cross layers

The current test suite is already strong in focused unit coverage, and it also
has meaningful integration-style coverage for build and watch flows.

What is still thinner than ideal is end-to-end scenario coverage for one feature
that should stay consistent across planning, evaluation, staging, and watch.

The excellent-bar target is a small set of canonical workspace scenarios that
assert the same fact through multiple layers, for example:

- a route and its redirect behavior
- a selected version context and its staged output
- an internal link rule as seen in both `check` and staged content

That kind of test catches cross-layer drift better than adding more helper-only
tests.

### 2. Verify documentation examples against real fixtures where possible

Right now the docs and the tests both contain useful examples, but they are not
tied together tightly enough.

For an excellent bar, the most important onboarding and how-to examples should be
grounded in reusable fixtures or generated output that the test suite already
knows how to build.

That does not mean testing every prose snippet. It means protecting the few
example packets that readers are most likely to copy.

## What still needs to change in the documentation

### 1. Keep the larger getting-started pages as concrete as the tiny-site docs

The docs root, concepts pages, and tiny-site onboarding are in much better shape
than before. The remaining reader-facing gap is that the larger size-band pages
are still more abstract than the tiny-site material.

For example, `site/pages/getting-started/tiny.md` already gives readers a small
workspace shape, a catalog example, commands to run, and staged files to inspect.
Pages like `medium.md` and `large.md` still lean more on reading paths and mental
models than on reusable example packets.

The excellent-bar target is for each size-band page to show:

- the smallest concrete repo shape for that band
- one representative `catalog.yaml` fragment
- the command the reader runs
- the first staged file or aggregate file to inspect

### 2. Add more maintainer-facing ownership notes in heavy internal modules

The maintenance pages are stronger now, but a few implementation-heavy modules
still rely too much on readers inferring boundaries from code alone.

The highest-value doc additions are short module-level notes for places like:

- `staging/coordinator.py`
- `evaluation/execution.py`
- `planning/build_plan.py`

Each note should explain:

- what the module owns
- what inputs it assumes are already validated
- what invariants it enforces itself
- what kind of object it is allowed to emit downstream

### 3. Keep maintenance notes current when cleanup lands

An excellent documentation bar is not only about adding new pages. It is also
about removing stale maintainer advice quickly.

If a refactor theme has already landed, the maintenance notes should stop talking
about it as open work and instead describe the smaller remaining gap.

This page exists partly to enforce that rule.

## What to prioritize next

If maintainers only take four next actions, start here:

1. replace `build_effective_build_plan()` with one explicit result object
2. split the remaining heavy orchestration in `staging/coordinator.py`
3. add two or three cross-layer scenario tests that assert one rule through
   planning, evaluation, staging, and watch
4. upgrade `medium.md` and `large.md` with real example packets and expected
   staged outputs

Those four changes would do the most to move the repo from "already strong" to
"excellent and easier to keep excellent".
