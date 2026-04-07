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

This codebase is already in the "strong" range and is now much closer to the
"excellent and maintainable" bar than it was earlier in the cleanup work.

The remaining gap is no longer broad correctness work or unclear major
boundaries. The main risk now is drift: one layer changes, the next layer still
passes its own unit tests, but the full reader-facing or operator-facing story
is no longer as obviously consistent as it should be.

That means the next quality step is mostly about protecting the best examples
and the most important cross-layer rules.

## Where the remaining gap still lives

### 1. Canonical cross-layer scenario coverage is still thinner than ideal

The current test suite is already strong in focused unit coverage, and it also
has meaningful integration-style coverage for build and watch flows.

What is still thinner than ideal is a small set of canonical scenario tests
where one rule is asserted through planning, evaluation, staging, and watch.

The excellent-bar target is a small set of canonical workspace scenarios that
assert the same fact through multiple layers, for example:

- a route and its redirect behavior
- a selected version context and its staged output
- an internal link rule as seen in both `check` and staged content

That kind of test catches cross-layer drift better than adding more helper-only
tests.

### 2. The highest-value documentation examples should be fixture-backed

The getting-started pages are now much more concrete, which is good. The next
step is to make the most copied example packets harder to drift away from the
tested reality.

For an excellent bar, the most important onboarding and how-to examples should
be grounded in reusable fixtures or generated output that the test suite already
knows how to build.

That does not mean testing every prose snippet. It means protecting the few
example packets that readers are most likely to copy.

### 3. Keep maintenance notes ruthless about current state

This page should stay short and current. If a cleanup theme no longer describes
the live repo, it should disappear from the note quickly instead of becoming a
historical checklist.

## What to prioritize next

If maintainers only take four next actions, start here:

1. add one canonical scenario for a selected version context from planning
   through staged output and watch reuse
2. add one canonical scenario for route or redirect behavior through check,
   staged aggregates, and watch
3. tie one copied documentation packet to reusable fixture-backed output
4. keep this note current whenever one of those themes lands

Those four changes would do the most to move the repo from "already strong" to
"excellent and resistant to drift".
