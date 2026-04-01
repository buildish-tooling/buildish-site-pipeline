# Copyright 2026 The Buildish Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Explicit worker-process entrypoint for first-wave owned-unit staging."""

from __future__ import annotations

import sys

from .ownership import OwnedUnitKind
from .units import (
    run_component_unit,
    run_site_assets_unit,
    run_site_pages_unit,
    run_vendor_assets_unit,
)
from .worker_protocol import WorkerResultWire, WorkerSpecWire, worker_failure_result


def execute_worker_spec(spec: WorkerSpecWire) -> WorkerResultWire:
    """Dispatch one worker spec and convert unexpected failures into wire results."""

    try:
        unit_kind = OwnedUnitKind(spec.unit_kind)
    except ValueError:
        return worker_failure_result(
            unit_id=spec.unit_id,
            category="unknownUnitKind",
            message=f"Unsupported worker unit kind: {spec.unit_kind}",
            stage_meta=spec.stage_meta,
        )

    try:
        if unit_kind is OwnedUnitKind.SITE_PAGES:
            return run_site_pages_unit(spec)
        if unit_kind is OwnedUnitKind.SITE_ASSETS:
            return run_site_assets_unit(spec)
        if unit_kind is OwnedUnitKind.VENDOR_ASSETS:
            return run_vendor_assets_unit(spec)
        return run_component_unit(spec)
    except (
        Exception
    ) as exc:  # pragma: no cover - exercised through the subprocess boundary.
        return worker_failure_result(
            unit_id=spec.unit_id,
            category=exc.__class__.__name__,
            message=str(exc) or exc.__class__.__name__,
            stage_meta=spec.stage_meta,
        )


def main() -> int:
    """Read one worker spec from stdin and write one worker result to stdout."""

    spec = WorkerSpecWire.model_validate_json(sys.stdin.read())
    result = execute_worker_spec(spec)
    sys.stdout.write(result.model_dump_json(by_alias=True))  # noqa: TID251
    sys.stdout.write("\n")  # noqa: TID251
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
