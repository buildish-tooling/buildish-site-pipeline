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

This codebase is already in the "very strong" range and the earlier cleanup
work removed most of the broad production, documentation, and testing gaps.

The remaining gap is no longer broad correctness work or unclear major
boundaries. The main risk now is narrow drift in the last few high-value
examples and cross-layer rules: one layer changes, the next layer still passes
its own unit tests, but the full reader-facing or operator-facing story is no
longer as obviously consistent as it should be.

That means the next quality step is mostly about protecting the last few
highest-value examples and the remaining cross-layer rules that still deserve a
canonical scenario.

## Where the remaining gap still lives

### 1. Cross-layer scenario coverage is better, but route and link rules still deserve canonical scenarios

The current test suite is already strong in focused unit coverage, and it also
has meaningful integration-style coverage for build and watch flows.

The selected-version path now has a real canonical scenario that is asserted
through planning, evaluation, staged aggregates, and watch.

What is still thinner than ideal is the remaining set of canonical scenarios
where route ownership or link policy should be asserted across multiple layers.

The excellent-bar target is a small set of canonical workspace scenarios that
assert the same fact through multiple layers, especially:

- a route and its redirect behavior
- an internal link rule as seen in both `check` and staged content

That kind of test catches cross-layer drift better than adding more helper-only
tests.

### 2. More than one copied documentation packet should be fixture-backed

The getting-started pages are now much more concrete, and the medium-site
packet is already tied to a reusable fixture-backed regression.

The remaining gap is smaller now: the next most-copied packet or two should get
the same treatment so the docs do not fall back to being accurate by memory.

For an excellent bar, the most important onboarding and how-to examples should
be grounded in reusable fixtures or generated output that the test suite already
knows how to build.

That does not mean testing every prose snippet. It means protecting the next few
example packets that readers are most likely to copy, such as `large.md` or one
of the high-traffic how-to pages.

### 3. Keep maintenance notes ruthless about current state

This page should stay short and current. If a cleanup theme no longer describes
the live repo, it should disappear from the note quickly instead of becoming a
historical checklist.

## What to prioritize next

If maintainers only take four next actions, start here:

1. add one canonical scenario for route or redirect behavior through check,
   staged aggregates, and watch
2. add one canonical scenario for an internal link rule through check
   diagnostics and staged content
3. tie one more copied documentation packet to reusable fixture-backed output
4. keep this note current whenever one of those themes lands

Those four changes would do the most to move the repo from "already strong" to
"excellent and resistant to drift".
