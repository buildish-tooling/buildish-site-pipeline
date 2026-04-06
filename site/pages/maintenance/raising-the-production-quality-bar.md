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

## Highest-leverage improvements

### 1. Reduce orchestration density

The biggest quality jump would come from keeping branch-heavy orchestration thin.
Large functions that parse inputs, apply policy, perform I/O, and map failures at
the same time are still understandable, but they are harder to review and easier
to drift.

Prefer:

- small pure decision helpers
- thin top-level orchestration that mostly wires calls together
- clear splits between normalization, policy, I/O, and diagnostic mapping

### 2. Encode more invariants in types and constructors

The code already validates a lot. The next step is to make more invalid states
hard to represent at all.

Prefer:

- dedicated value types or enums over semantically overloaded raw strings
- constructors or validators that only return already-safe objects
- fewer partially valid objects that require repeated later revalidation

### 3. Centralize trust-boundary rules more aggressively

Path safety, symlink handling, output-root rules, publication safety, and other
trust checks should stay single-sourced. The quality bar rises when maintainers
can point to one obvious helper for each sensitive rule and know that nearby code
is not re-implementing a slightly different version.

Prefer:

- one canonical helper per trust rule
- shared reuse instead of similar local checks
- explicit documentation of which helper is the source of truth

### 4. Single-source policy across planning, evaluation, and staging

Some rules naturally span multiple layers, especially selection, publication,
route resolution, readiness, and shared validation. The codebase gets stronger
when those rules are interpreted in one place and reused rather than mirrored in
parallel implementations.

Prefer:

- one canonical decision path for each major policy
- shared helpers for route, selection, and publication semantics
- refactors that remove parallel interpretations of the same contract

### 5. Make lifecycle transitions more explicit

Watch, build, and stage behavior is already careful, but the quality bar rises
again when state transitions are easier to see and harder to misuse.

Prefer:

- explicit transition helpers or state-machine-like structure
- fewer implicit flag combinations
- stronger assertions around allowed transition paths

## Secondary improvements that still matter

### 6. Add more maintainer-facing module docs

Short internal docs should make it obvious:

- what a module owns
- what it assumes is already validated
- what it must revalidate itself
- what public data it is allowed to emit

### 7. Add deliberate internal impossibility checks

Good validation at the edges is not enough. Internal contradictions should also
fail loudly so contract drift is caught early during development and review.

### 8. Prune defensive fossils when they stop paying for themselves

After long audit or hardening waves, some modules naturally collect extra guards
and fallback branches. Periodic cleanup should remove defensive code that is no
longer meaningfully reachable or no longer explains a real invariant.

## What to prioritize first

If maintainers only take three actions, start here:

1. refactor orchestration-heavy modules into smaller decision layers
2. encode more invariants in types and constructors
3. centralize trust and path-safety rules into fewer canonical helpers

These three shifts give the biggest payoff in reviewability, refactor safety, and
long-term semantic consistency.
