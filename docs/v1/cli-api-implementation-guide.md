---
weight: 32
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

# CLI and invocation-API implementation guide

This document tells implementers how to build the `site-pipeline` command-line
interface and its internal invocation layer.

It is intentionally prescriptive. The goal is that a junior engineer can follow
it directly without inventing local rules for command parsing, exit-code
handling, report emission, or watch-mode failure behavior.

This guide complements:

- `api-contract.md` as the source of truth for the public invocation boundary
- `planning-and-input-resolution-implementation-guide.md` for the planning,
  local-input resolution, and build-plan-candidate layer below the CLI
- `validation-and-check.md` for `check` semantics and diagnostics
- `evaluation-and-validation-implementation-guide.md` for the shared contextual
  validation and stage-gating layer
- `build-architecture.md` for the shared execution path below the CLI
- `watch-incremental-staging-plan.md` for watch-cycle safety and reporting rules
- `security-and-trust-model.md` for path, trust, and output-safety requirements
- `model-implementation-guide.md` for report-model loading and serialization

## Scope

This guide is about the public `site-pipeline` executable and the internal
Python modules that parse invocations, dispatch commands, and emit text or JSON
reports.

It covers:

- the stable command surface,
- parser structure,
- option validation,
- stdout/stderr discipline,
- exit-code mapping,
- machine-readable report emission,
- watch-mode command behavior,
- CLI-facing security checks, and
- tests for the command layer.

It does **not** define:

- the staged-output schema,
- the model schema,
- the planning/build/watch engine internals, or
- any public Python library API.

## Fixed decisions

Implementers should treat the following as already decided:

1. The only stable public invocation API is the `site-pipeline` executable.
2. The stable first-wave commands are `plan`, `check`, `build`, and `watch`.
3. The internal Python package is **not** a public API.
4. `site-pipeline serve` is intentionally out of scope.
5. `preview` is not part of the stable contract and must not shape the stable CLI
   design.
6. `check`, `build`, and each `watch` cycle share one execution pipeline until
   stage mutation begins.
7. Machine-readable reports use the typed report models from the schema and model
   guides; the CLI must not hand-roll ad hoc JSON dictionaries.
8. Report schema-version selection is explicit; JSON report output does not guess
   a schema version implicitly.
9. Watch mode must preserve the last-known-good stage when safe and exit when
   stage integrity becomes ambiguous.

## Required package layout

The first implementation wave should keep the public entry point thin and move
real logic into dedicated internal modules.

Required layout:

- `apache_buildish_site_pipeline/__main__.py`
- `apache_buildish_site_pipeline/cli.py`
- `apache_buildish_site_pipeline/cli_contract.py`
- `apache_buildish_site_pipeline/cli_parser.py`
- `apache_buildish_site_pipeline/cli_dispatch.py`
- `apache_buildish_site_pipeline/cli_output.py`
- `apache_buildish_site_pipeline/cli_reporting.py`
- `apache_buildish_site_pipeline/cli_errors.py`
- `apache_buildish_site_pipeline/commands/__init__.py`
- `apache_buildish_site_pipeline/commands/plan.py`
- `apache_buildish_site_pipeline/commands/check.py`
- `apache_buildish_site_pipeline/commands/build.py`
- `apache_buildish_site_pipeline/commands/watch.py`

The command modules should call into the shared planning, validation, and staging
engine. They should not re-implement engine logic inside the CLI package.

## Responsibility split inside the CLI layer

Use this split consistently.

### `__main__.py`

- imports `main` from `cli.py`
- exits with `SystemExit(main())`
- contains no parsing or business logic

### `cli.py`

- exposes `main(argv: list[str] | None = None) -> int`
- orchestrates parse, dispatch, output emission, and exit-code mapping
- does not call `sys.exit()` directly

### `cli_parser.py`

- builds the parser
- converts parsed arguments into immutable invocation objects
- rejects invalid option combinations as invocation failures

### `cli_contract.py`

- defines immutable invocation types such as `PlanInvocation`,
  `CheckInvocation`, `BuildInvocation`, and `WatchInvocation`
- defines shared enums such as report format and application-owned exit codes
- defines shared report-request structures

### `cli_dispatch.py`

- maps one invocation object to exactly one command handler
- contains no argument parsing
- contains no direct filesystem write logic except command-level report emission

### `cli_output.py`

- renders human-oriented text output
- ensures JSON-to-stdout mode does not mix with human chatter
- owns stream-selection rules for stdout versus stderr

### `cli_reporting.py`

- serializes typed report models to JSON or stable text snapshots
- validates and writes report files safely
- owns same-directory temporary write plus atomic replace for report files

### `cli_errors.py`

- defines the small error taxonomy used by `main()`
- avoids sprinkling raw `ValueError` and ad hoc exit-code decisions everywhere

### `commands/*.py`

- adapt CLI invocations to the shared engine
- receive typed command results from the engine
- build typed report models and summary objects
- do not parse command-line arguments or print directly

## Parser and command-shape rules

The CLI should use the Python standard library parser for the first
implementation wave.

Recommended parser policy:

- use `argparse`, not ad hoc `sys.argv` parsing
- prefer an `ArgumentParser(exit_on_error=False)` configuration or equivalent so
  `main()` retains ownership of exit-code mapping
- set `allow_abbrev=False` so partial long-option spellings are rejected instead
  of guessed
- configure the parser so argument failures are surfaced to `main()` and mapped
  to exit code `2` rather than causing deep parser-owned process exits
- use subcommands for `plan`, `check`, `build`, and `watch`
- make the subcommand required
- use kebab-case for CLI flags
- use explicit `choices=` for enum-like option values
- do not let the parser call `sys.exit()` deep inside application logic; convert
  parser failures into application exit code `2`

### Supported first-wave commands

The stable first-wave public commands are:

- `site-pipeline plan`
- `site-pipeline check`
- `site-pipeline build`
- `site-pipeline watch`

Do not add stable `serve` or other renderer-owning commands.

### Shared report flags

Implement one shared report-option group for every report-capable command:

- `--report-format`
- `--report-schema-version`
- `--report-output`

Required rules:

- `--report-format` accepts `text` or `json`
- `--report-schema-version` is required when `--report-format json` is selected
- unsupported requested schema versions fail with exit code `2` before expensive
  workspace evaluation begins
- `--report-schema-version` must be rejected when `--report-format` is not
  `json`; do not silently ignore it
- `--report-output` defaults to `-` unless a command-specific rule overrides it
- `watch --report-format json --report-output -` is invalid and must fail with
  exit code `2`

When `--report-output` is a file path, the selected format may be written there
for any report-capable command. JSON is the stable automation format. Text file
snapshots are human-oriented convenience output only.

### Command-specific flags

Required first-wave command-specific flags:

- `plan --for {build,watch}`
- `check --fail-on {error,warning}`

Do not add undocumented stable command flags in the first implementation wave.
If a temporary internal or experimental flag is needed during development, keep
it clearly marked as non-stable and do not let it redefine the public contract.

## Required invocation objects

The parser should convert raw arguments into typed immutable invocation objects.

At minimum define:

- `PlanInvocation`
- `CheckInvocation`
- `BuildInvocation`
- `WatchInvocation`
- `ReportRequest`

Each invocation object should already represent a valid command. That means:

- parser-level option normalization is complete,
- invalid combinations are already rejected,
- default values are already explicit,
- downstream handlers do not need to re-parse strings such as `warning` or
  `build`.

## Exit-code contract

The CLI layer owns the stable application exit-code contract.

Use exactly these application-owned exit codes:

- `0`: success under the command's documented success criteria
- `1`: domain failure for commands that define a normal failing result
- `2`: invalid invocation, invalid option combination, or unsupported requested
  report schema version
- `3`: internal failure or unrecoverable integrity failure

Do not invent additional application-owned exit codes.

### Command-specific mapping

#### `plan`

- `0`: planning completed and produced a report, even if entries are `missing`,
  `stale`, or `unresolved`
- `1`: planning completed but found error diagnostics that prevent a usable plan
- `2`: invalid invocation or unsupported requested report schema version
- `3`: internal failure while evaluating the workspace

#### `check`

- `0`: validation completed and satisfied the active failure threshold
- `1`: validation completed but failed the active failure threshold
- `2`: invalid invocation or unsupported requested report schema version
- `3`: internal failure while evaluating the workspace

#### `build`

- `0`: build completed and produced a trustworthy finalized stage
- `1`: build completed evaluation but found error diagnostics or staging failures
  that prevented a usable finalized stage
- `2`: invalid invocation or unsupported requested report schema version
- `3`: internal failure or unrecoverable stage-integrity failure

#### `watch`

- `0`: orderly application-controlled shutdown after watch steady state started
- `2`: invalid invocation or unsupported requested report schema version
- `3`: internal failure or unrecoverable stage-integrity failure

`watch` should not normally use application-owned exit code `1`. Ordinary cycle
failures should be reported in the refreshed `StageRunReport` while the process
keeps watching.

### Signal handling rule

Do not remap external signal termination into invented application exit codes.

If the implementation allows the process to terminate due to an external signal,
the resulting shell status is outside the application-owned `0` through `3`
range. If the implementation later adds graceful signal handling, it must not
lie about stage integrity while shutting down.

## Shared execution-path rule

The CLI must preserve one command-to-engine mapping:

- `plan`: planning only
- `check`: resolve, validate, summarize
- `build`: resolve, validate, stage, summarize
- `watch`: resolve, validate, stage, summarize repeatedly

The CLI must **not** create a second validation path for `check` or a second
staging path for `watch`.

That means the command handlers should call into shared execution functions below
the CLI boundary rather than implementing custom side paths.

## Output-stream discipline

This is a correctness requirement, not presentation polish.

### Human-oriented output

Recommended rules:

- normal human-readable command output may go to stdout
- invocation and usage errors should go to stderr
- unexpected internal-failure summaries should go to stderr
- help output may use stdout in the normal CLI way

Text output is for humans and may evolve. Automation should use JSON reports,
not screen-scraped text.

### JSON output

When `--report-format json --report-output -` is selected for a non-watch
command, stdout must contain exactly one valid JSON document and nothing else.

That means:

- no banners,
- no progress chatter,
- no debug logging,
- no warning prefaces,
- no extra trailing text.

Any optional human-oriented notices must go to stderr or be suppressed.

### Watch command stream rules

For `watch`, repeated machine-readable reporting is file-oriented. The command
must not stream multiple JSON documents to stdout as the stable report API.

Required rules:

- `watch --report-format json` requires a file `--report-output`
- human-oriented watch status may be written to stderr
- any requested report file must be rewritten as one complete snapshot after the
  initial cycle and after each later completed cycle

## Report-model rules

Use the typed models defined in the schema and model guides.

Required command-to-report mapping:

- `plan` JSON report -> `ResolvedMaterializationReport`
- `check` JSON report -> `CheckReport`
- `build` JSON report -> `StageRunReport` with `command: build`
- `watch` JSON report -> `StageRunReport` with `command: watch`

Do not assemble raw untyped dictionaries in the CLI layer.

### Fixed report-field rules

At minimum, the CLI/API layer must enforce:

- `ResolvedMaterializationReport.target` matches the requested `plan --for`
- `ResolvedMaterializationReport.entries[*].watchEligible` is present on every
  entry when `target = watch`
- `CheckReport.command = check`
- `StageRunReport.command = build` or `watch` according to the actual command
- `StageRunReport.cycle` is omitted for `build`
- `StageRunReport.cycle` is present for `watch`
- `StageRunSummary` normative combinations match the schema-reference contract
- `CheckSummary.failOnSeverity` reflects the selected `--fail-on` threshold
- `check --fail-on warning` changes only pass/fail threshold behavior; it does
  not rewrite diagnostic severities in the report
- every emitted JSON report includes the effective requested `schemaVersion`

## Safe report-file writing

Report emission is a write path and must follow path-safety rules.

When `--report-output` is a file path, the CLI layer must:

1. normalize the path before use,
2. reject traversal, ambiguous relative-target behavior, or other path forms that
   do not resolve cleanly to the intended final file path,
3. resolve symlinks before trust decisions and reject final write targets that
   resolve through a symlink,
4. create same-directory temporary files for replacement writes,
5. write complete UTF-8 content to the temp file,
6. flush and finalize the temp file before replace,
7. atomically replace the destination,
8. never leave a partial JSON or partial text report at the final path.

Report outputs must live outside the finalized stage root. They are
operator-facing sidecar outputs, not part of the staged-tree contract.

For watch mode, report outputs should also live outside the pipeline-owned watch
work area.

For `watch`, perform that validation again before each report rewrite, not only
at startup.

If a watch report file lives beneath a broader watched workspace tree, the watch
filter must explicitly exclude that report path so report rewrites cannot retrigger
fresh cycles.

If a caller-selected report file path is invalid at invocation time, fail with
exit code `2`. If a previously accepted path becomes unsafe or unwritable during
execution, treat that as an execution failure. In watch mode, that can require a
hard exit if the report destination is part of the trustworthy operator-facing
state for the running process.

## Command-specific behavior rules

### `plan`

`plan` is non-mutating except for the optional requested report output.

It must not:

- fetch from SCMs or providers,
- mutate caches,
- materialize missing inputs,
- write or partially write a stage tree.

Its job is to answer what local inputs are required and what their readiness
states are.

### `check`

`check` is non-mutating except for the optional requested report output.

It must stop before:

- stage-root preparation,
- file copying,
- aggregate metadata writes,
- `manifest.json` creation,
- watch-loop startup.

It must reuse the same validation logic that `build` and `watch` depend on.

### `build`

`build` is the one-off stage-producing command.

The CLI/API layer must ensure that a successful `build` result means:

- a trustworthy finalized stage exists,
- `manifest.json` has been written last,
- any requested report has been emitted consistently with that result.

If stage integrity becomes ambiguous, return exit code `3`, not `1`.

### `watch`

`watch` is a long-running orchestration command over the same staging engine.

The CLI/API layer must respect the watch-state outcomes defined in
`watch-incremental-staging-plan.md`.

Required behavior:

- if the initial cycle fails before any trustworthy stage exists, exit with `3`
- if an ordinary later cycle fails but the prior stage remains trustworthy, keep
  running and refresh the report to show cycle failure
- if a later cycle leaves stage integrity ambiguous, exit with `3`
- if a report file is requested, rewrite it after the initial cycle and after
  each later completed cycle
- do not claim a fresh stage write in the report when the cycle retained the
  last-known-good stage instead

## CLI-facing security rules

The command layer is not where all security validation happens, but it owns some
important boundaries.

### Never trust command output destinations blindly

The CLI layer must validate caller-selected report destinations before writing.

It must reject:

- output paths that escape the intended owned location,
- final targets that resolve through a symlink,
- invalid `watch` JSON stdout requests,
- output plans that would knowingly leave a partial final report.

### Keep operator policy local

Local operator execution policy must stay local.

That means:

- report schema-version selection comes from CLI invocation, not repo metadata,
- watch polling controls such as `WATCHFILES_FORCE_POLLING` remain local
  environment policy, not repo-authored input,
- safe-default overrides defined by the security docs must not come from
  provider data or authored site metadata.

### Avoid leaking machine-local details unnecessarily

Human error summaries and JSON reports should not add extra machine-local detail
beyond the documented contract.

In particular:

- do not emit Python tracebacks by default for expected invocation failures,
- do not dump internal filesystem layout details into public staged aggregate
  outputs through the CLI layer,
- do not mix debug noise into machine-readable stdout JSON.

If a debug mode is later added, it must remain a local operator-controlled tool,
not a repo-authored behavior change.

### Separate text rendering from trust decisions

Human-facing diagnostic messages are text, not trusted markup.

The CLI layer should print them as plain text and must not invent any HTML or
terminal escape behavior that turns untrusted metadata into active content.

## Recommended error taxonomy

Use a small explicit error taxonomy instead of broad accidental exception
mapping.

At minimum define:

- `InvocationError` -> exit `2`
- `UnsupportedReportSchemaVersionError` -> exit `2`
- `CommandExecutionError` -> exit `3` unless the command contract maps it to a
  normal domain failure
- `StageIntegrityError` -> exit `3`
- `ReportWriteError` -> exit `3` once execution has started

Normal domain failures that are reflected in typed reports, such as failing
validation under `check` or a non-usable `build`, should become command results,
not uncaught exceptions.

## Required implementation order

Implementers should follow this order.

### Phase 0: parser and contract skeleton

1. Keep `__main__.py` as a thin wrapper.
2. Turn `cli.py` into a thin `main(argv) -> int` orchestrator.
3. Add `cli_contract.py`, `cli_parser.py`, `cli_dispatch.py`, `cli_errors.py`,
   `cli_output.py`, and `cli_reporting.py`.
4. Define immutable invocation objects and exit-code enums.
5. Implement the parser with subcommands and shared report options.
6. Add parser tests before adding real command handlers.

### Phase 1: stable `plan` and `check` command layer

1. Implement `commands/plan.py` and `commands/check.py`.
2. Hook them to the shared resolve/validate pipeline.
3. Emit typed text summaries and typed JSON reports.
4. Prove that JSON stdout mode emits exactly one JSON document.
5. Prove that invalid option combinations fail with exit code `2`.

### Phase 2: stable `build` command layer

1. Implement `commands/build.py`.
2. Map build outcomes to `0`, `1`, and `3` exactly as documented.
3. Emit typed `StageRunReport` output.
4. Validate requested report-file writes safely.
5. Prove that manifest/report success signals align with finalized-stage success.

### Phase 3: stable `watch` command layer

1. Implement `commands/watch.py`.
2. Reuse the same engine path as `build`.
3. Implement initial-cycle failure behavior.
4. Implement ordinary-cycle retained-stage behavior.
5. Implement hard-exit behavior for ambiguous stage integrity.
6. Implement per-cycle report rewrites.
7. Add tests for cycle-result to exit/report mapping.

## Required test layout

The test layout should mirror the CLI modules:

- `tests/cli/test_parser.py`
- `tests/cli/test_main.py`
- `tests/cli/test_output.py`
- `tests/cli/test_reporting.py`
- `tests/cli/test_dispatch.py`
- `tests/cli/test_plan_command.py`
- `tests/cli/test_check_command.py`
- `tests/cli/test_build_command.py`
- `tests/cli/test_watch_command.py`

## Required tests per concern

### Parser tests

Test at least:

- missing subcommand,
- unknown command,
- unknown option,
- rejected option abbreviation,
- invalid enum choice,
- `--report-format json` without `--report-schema-version`,
- `--report-schema-version` with non-JSON output,
- `watch --report-format json --report-output -`,
- `plan --for` required behavior,
- `check --fail-on` value handling.

### `main()` tests

Test at least:

- return codes instead of deep `sys.exit()` behavior,
- invocation errors map to `2`,
- internal failures map to `3`,
- JSON stdout mode emits one valid JSON document and no extra text,
- human error output goes to stderr,
- `python -m apache_buildish_site_pipeline` delegates correctly.

### Report-writing tests

Test at least:

- same-directory temp-file replacement,
- rejection of symlinked final targets,
- rejection of escape attempts,
- UTF-8 writing,
- atomic replacement preserving a valid final file,
- watch repeated rewrites after multiple cycles,
- failure behavior when the report destination becomes unsafe mid-run.

### Command behavior tests

Test at least:

- `plan` does not start staging,
- `check` stops before stage mutation,
- `build` success emits `StageRunReport.command = build`,
- `watch` success emits `StageRunReport.command = watch`,
- `build` omits `cycle`,
- `watch` includes `cycle`,
- failed `check` returns `1` without being treated as internal failure,
- failed `build` returns `1` when the result is a normal non-usable stage
  outcome,
- stage-integrity failures return `3`,
- ordinary `watch` cycle failures keep the process alive and refresh the report,
- initial watch-cycle failure with no trustworthy stage exits with `3`.

## Review checklist before merging CLI/API code

### Contract shape

- [x] only `plan`, `check`, `build`, and `watch` are treated as stable commands
- [x] `serve` is not added as a stable command
- [x] the public Python package surface is not documented as stable API
- [x] shared report flags behave consistently across commands

### Correctness

- [x] `main(argv)` returns application exit codes
- [x] parser failures become exit `2`
- [x] the command layer reuses the shared engine path
- [x] `check` stops before stage mutation
- [x] `build` success really means a trustworthy finalized stage exists
- [x] `watch` distinguishes retained-failure from exit-required failure
- [x] JSON stdout mode never mixes with human chatter

### Security

- [x] report destinations are normalized and validated before writing
- [x] final report targets do not resolve through symlinks
- [x] same-directory temp writes are used for report replacement
- [x] operator-policy inputs stay local to CLI/env surfaces
- [x] no unexpected debug/path leakage is added to machine-readable output
- [x] watch report rewrites revalidate the destination each cycle

### Test coverage

- [x] parser negative cases are covered
- [x] JSON stdout exactness is covered
- [x] report-write safety is covered
- [x] exit-code mapping is covered
- [x] watch initial-cycle and retained-failure behavior is covered

## Bottom line

If implementers follow this guide, the result should be:

- one thin stable `site-pipeline` CLI boundary,
- one clear split between parsing, dispatch, output, and engine logic,
- consistent application-owned exit codes,
- safe report emission,
- watch behavior that does not lie about stage integrity, and
- a command layer that is testable without pretending internal Python modules are
  a public API.