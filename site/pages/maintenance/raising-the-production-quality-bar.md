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

This codebase is already in the "strong" range. The main remaining gap is no
longer broad correctness or missing validation. It is making the current design
easier to keep correct, easier to review, and easier for new maintainers to
understand without reading several modules side by side.

The current architecture already relies on explicit contracts between planning,
evaluation, staging, and watch. The next step is to make the most important
reader paths just as clear as the runtime paths.

## What still needs to change in production code

### 1. Keep shrinking the remaining heavy orchestration modules

The largest production-code hotspot is still `src/apache_buildish_site_pipeline/evaluation/execution.py`.
It owns important decisions, but it also still carries enough phase ordering,
policy application, and report assembly that review work is heavier than it
should be.

The same pattern can still appear in a few adjacent modules, but evaluation is
the clearest place where the excellent-bar target is still visible.

The target remains:

- top-level functions that mostly wire phases together
- phase-local result objects instead of ad hoc handoff shapes
- decision helpers that separate policy from filesystem mutation or report
  assembly

### 2. Keep internal boundaries small and explicit

The codebase now depends on a small number of high-value internal contracts:

- planning outputs that evaluation can trust
- evaluation outputs that staging can publish safely
- worker results and aggregate manifests that staging can combine deterministically

The excellent-bar target is to keep those boundaries narrow, typed, and obvious
to readers. New compatibility branches, fallback shapes, or hidden implicit
assumptions should only exist when they protect a real documented boundary.

## What still needs to change in the test codebase

### 1. Put more weight on canonical scenario tests that cross layers

The current test suite is already strong in focused unit coverage, and it also
has meaningful integration-style coverage for build and watch flows.

What is still thinner than ideal is feature-level scenario coverage for one rule
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

The remaining reader-facing gap is that the larger size-band pages are still
more abstract than the tiny-site material.

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

A few implementation-heavy modules still rely too much on readers inferring
boundaries from code alone.

The highest-value doc additions are short module-level notes for places like:

- `evaluation/execution.py`
- `staging/aggregates.py`
- `planning/build_plan.py`

Each note should explain:

- what the module owns
- what inputs it assumes are already validated
- what invariants it enforces itself
- what kind of object it is allowed to emit downstream

### 3. Keep maintenance notes current when cleanup lands

An excellent documentation bar is not only about adding new pages. It is also
about removing stale maintainer advice quickly.

When a refactor theme no longer reflects the live codebase, the maintenance notes
should stop describing it as active work and instead describe the current
remaining gap.

This page exists partly to enforce that rule.

## What to prioritize next

If maintainers only take four next actions, start here:

1. tie one high-value documentation example to reusable fixture-backed output
2. upgrade `medium.md` and `large.md` with real example packets and expected
   staged outputs
3. add one short ownership-and-invariants note to `evaluation/execution.py` or
   another implementation-heavy module
4. add two or three more cross-layer scenario tests that assert one rule through
   planning, evaluation, staging, and watch

Those four changes would do the most to move the repo from "already strong" to
"excellent and easier to keep excellent".
