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

# Contributing to Buildish

Thank you for considering a contribution to Buildish.

## Prerequisites

The repository checks use:

- Python 3.13 or newer, matching `pyproject.toml`;
- [uv](https://docs.astral.sh/uv/) for the locked Python environment;
- GNU Make for the documented task entrypoints;
- Java 21 or newer, `curl`, and `tar` for the Apache RAT license check; and
- Git for source-control checks.

The first RAT run downloads the pinned Apache RAT archive and verifies its
SHA-512 checksum. Container-engine and multi-platform emulation prerequisites
are needed only for the optional image workflows.

Create or refresh the repository environment with:

```bash
uv sync --frozen
```

Then inspect the curated workflows with:

```bash
make help
```

## Development workflow

Run the narrowest relevant test while iterating. Existing environments can run
individual test modules without changing dependency state, for example:

```bash
.venv/bin/python -m unittest tests.test_getting_started_docs -v
```

Before treating a change as complete, run the repository gate:

```bash
make check
```

That gate runs Ruff, mypy, the Python unit tests, Apache RAT, and the
checked-in preliminary release-legal verification. It should leave the worktree
unchanged. If you intentionally change a generated file contract, regenerate
the schemas and model reference with `make schemas`, review the diff, and then
rerun `make check`.

Renderer integration guides have different verification levels. Hugo has a
documented direct mount integration, Roq uses a documented consumer-side
adapter, and the Jekyll and MkDocs pages remain planned-guide stubs. Do not
describe a renderer as turnkey until its actual directory, routing, and local
development contracts are tested.

## Before opening a pull request

- Check whether an existing issue or pull request already covers the change.
- For larger changes, start a short design discussion on a GitHub issue before investing heavily in implementation.
- Keep pull requests focused; split unrelated work into separate changes.

## Pull request expectations

- Base pull requests on `main`.
- Describe the motivation and the change clearly.
- Add or update tests and documentation when applicable.
- Keep commit messages and pull request text readable for future project history.
- Report any relevant check that could not be run and why.

## Security issues

Do **not** open a public issue for a suspected security vulnerability. Instead, report it to [security@buildish.org](mailto:security@buildish.org).
