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

# Buildish Site Pipeline container image

This directory contains the reusable container image definition for the generic `site-pipeline` CLI runtime.

The image intentionally stays renderer-agnostic. It installs the extracted Python package and exposes the `site-pipeline` entrypoint, but it does **not** bundle Hugo, Node, consumer layouts, themes, or publishing logic.

That split keeps the image useful for container-first CI pipelines while letting consumers build their own derived images with renderer-specific tooling on top.

## Runtime user contract

The published runtime image now starts as a dedicated non-root `site-pipeline`
user. That reduces the blast radius for normal CLI execution and avoids
creating root-owned files in writable container-local paths.

Consumers that build derived images can still switch to `USER root` for package
installation or other privileged image-build steps, then switch back to
`USER site-pipeline` for the final runtime layer.

When a host workspace is bind-mounted at `/workspace`, the usual container file
permission rules still apply. If a downstream environment needs a specific
numeric UID/GID mapping, it can continue to override the runtime user with the
container engine's normal `--user` option.

## Local multi-platform image build script

Use `build-image.sh` for the actual image automation.

- Default platforms: `linux/amd64,linux/arm64`
- Default engine selection: `podman`, then `docker`
- Publishing is opt-in via `--push`

Examples:

- `tools/site-pipeline-image/build-image.sh --image ghcr.io/example/buildish-site-pipeline:latest --dry-run`
- `tools/site-pipeline-image/build-image.sh --engine podman --image ghcr.io/example/buildish-site-pipeline:latest`
- `tools/site-pipeline-image/build-image.sh --engine docker --image ghcr.io/example/buildish-site-pipeline:latest --push`

Local multi-platform builds may require binfmt/QEMU support on the host.

For `podman`, the build script builds each target platform sequentially into a manifest list and fails early with a clear prerequisite error if required binfmt/QEMU handlers are missing.

## Local publish testing with a localhost registry

The script is safe by default:

- no publishing happens unless `--push` is provided
- insecure publishing is disabled unless `--allow-insecure-localhost-registry` is also provided
- insecure publishing is only allowed for explicit localhost or loopback registry references

Current support:

- localhost insecure publish testing is supported with `podman`
- `docker` remains limited to the normal secure publish path

Example once you have a localhost registry listening on port `5000`:

- `tools/site-pipeline-image/build-image.sh --engine podman --image localhost:5000/buildish-site-pipeline:test --push --allow-insecure-localhost-registry`

## Reusable localhost registry integration test

Use `test-local-registry.sh` to exercise the full local publish path end to end.

It will:

- start a pinned local registry container bound only to `127.0.0.1`
- invoke `build-image.sh` with explicit localhost insecure-push opt-in
- fetch the published manifest list from the registry API
- verify that `linux/amd64` and `linux/arm64` were published
- clean up the local registry container automatically unless `--keep-registry` is used

The pinned local registry image reference is sourced from `tools/site-pipeline-image/Containerfile-local-registry` so Renovate can manage it.

## GitHub Actions

`.github/workflows/ci.yml` runs `make check`, builds the multi-platform image for
`linux/amd64` and `linux/arm64`, and publishes it to GHCR on trusted pushes to
the canonical repository.

## Preliminary image legal review helper

For release preparation, the repository also provides a preliminary legal
review helper via:

- `make release-legal-preliminary`

That helper derives the runtime dependency set from `uv.lock`, inspects the
installed Python distributions in the current environment, and writes draft
`LICENSE` / `NOTICE` files under `dist-release-legal/preliminary/`.

The supporting generated inventory plus copied legal texts stay under
`dist/release-legal-preliminary/`.

The generated files are deliberately review-oriented and must be checked by a
human before they are used in any published container image or other binary
distribution.

The final image build copies `dist-release-legal/LICENSE` and
`dist-release-legal/NOTICE` into the container image. See
`docs/maintenance/release-legal.md` for the maintainer workflow that connects
the preliminary generator output with those final files.
