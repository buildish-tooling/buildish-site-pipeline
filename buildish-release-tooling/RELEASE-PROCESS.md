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

# Site Pipeline Release Process

This draft applies the Buildish release architecture to `buildish-site-pipeline`.

## Special rule for this component

This component produces:

- the official ASF source release
- Python `sdist` and wheel artifacts
- a container image

The final exact Git tag should stay on the same source commit as the released RC. Secondary targets
then rebuild from that exact source commit.

## Release branches

Use the Buildish standard release branches:

- `release/1.x`
- `release/1.2.x`

## Draft workflow set

### `Create release branch`

Inputs:

- `release_line`
- `source_ref`

### `Prepare RC`

Inputs:

- exact `version`
- optional `source_sha`

Behavior:

- resolve the source from `source_sha` if provided
- otherwise prefer `release/1.2.x`, then `release/1.x` for version `1.2.3`
- hard-gate the workflow on successful or skipped GitHub checks for the resolved source commit
- derive the next RC number after the highest existing RC for the version, or `0` if none exists
- clean pre-existing RC staging directories for this version from ASF SVN before staging the new RC
- rely on release-branch CI instead of rerunning tests in the draft `Prepare RC` job
- build the reproducible source archive from Git using the shared `buildish-release-tooling`
  component
- sign the source archive with `gpg` using `BUILDISH_GPG_PRIVATE_KEY`
- stage the source archive, `.sha512`, and `.asc` into ASF SVN using
  `BUILDISH_SVN_DEV_USERNAME` / `BUILDISH_SVN_DEV_PASSWORD`
- create or re-create the draft GitHub Release for the final exact version
- emit GitHub Summary blocks for:
  - vote email templates
  - source artifact SHA512
  - source artifact detached ASCII-armored signature
  - RC verification commands

### `Verify RC`

This is authored as a bash script for trusted local Linux/macOS execution and may also be used from
a manual workflow.

### `Release version`

Inputs:

- exact `version`

Behavior:

- resolve the latest RC for the version
- promote the exact source release from Apache `dist/dev` to `dist/release`
- prune older releases from the same release line out of Apache `dist/release`
- create the final exact tag on the exact same source commit as the RC
- finalize the draft GitHub Release
- publish the Python artifacts to PyPI in a dedicated job
- publish the container image to Docker Hub in a dedicated job
- if moving aliases are enabled, derive `1` and `1.2` from the final version and update them in a
  dedicated job
- only update `latest` when `LATEST_TAG_ENABLED=true`; it is policy-driven and is disabled by
  default in this draft
- emit GitHub Summary blocks for:
  - source artifact SHA512
  - source artifact detached ASCII-armored signature
  - archived same-line releases
  - final PyPI and image URLs

## Files in this draft

- `buildish-release-tooling/release-config.yaml`: component policy consumed by
  `buildish-release-tooling`
- `buildish-release-tooling/release-tooling.sh`: a thin bash dispatcher that locates the component
  policy and runs `uv run --project <resolved-tooling-checkout> --frozen buildish-release-tooling
  <command> ...`
- `workflows/`: draft workflow YAML showing job boundaries and retries; the jobs install `uv`,
  fetch full Git state, and invoke the component wrappers
- `../buildish-release-tooling/tests/`: shared Python unit and integration tests that load this
  component's real `buildish-release-tooling/release-config.yaml` and smoke-test
  `buildish-release-tooling/release-tooling.sh`
