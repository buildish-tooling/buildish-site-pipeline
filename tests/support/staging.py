# Copyright 2026 The Apache Software Foundation
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

"""Shared staging helpers reused by staging and watch tests."""

from __future__ import annotations

import json
from pathlib import Path

from apache_buildish_site_pipeline.commands.shared import load_workspace_inputs
from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from apache_buildish_site_pipeline.models.enums import PlanningTarget, StageCommand
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.types import (
    BuildRequest,
    OperatorPolicy,
    StageDestination,
    WorkRootLayout,
)


def _build_request(workspace_root: Path, *, pool_size: int) -> BuildRequest:
    loaded_inputs = load_workspace_inputs(workspace_root)
    planning = evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=workspace_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=workspace_root / f"site/.stage-{pool_size}",
        work_root=workspace_root / f".buildish/work-{pool_size}",
    )
    evaluation = run_evaluation(
        request=EvaluationRequest(mode=EvaluationMode.BUILD),
        planning=planning,
    )
    if evaluation.build_plan is None:
        raise AssertionError("expected a build plan for the staging worker test fixture")
    return BuildRequest(
        command=StageCommand.BUILD,
        build_plan=evaluation.build_plan,
        diagnostics=evaluation.diagnostics,
        provider_snapshot=loaded_inputs.provider_snapshot,
        destination=StageDestination(
            stage_root=workspace_root / f"candidate-stage-{pool_size}",
        ),
        operator_policy=OperatorPolicy(pool_size=pool_size),
    )


def _expand_workspace_for_multiple_owned_units(workspace_root: Path) -> None:
    components_path = workspace_root / "site/components.yaml"
    authored = components_path.read_text(encoding="utf-8")
    components_path.write_text(
        authored.replace(
            "site: {}",
            "site:\n"
            "  pagesRoot: site/root-pages\n"
            "  assetsRoot: site/root-assets\n"
            "  vendorAssets:\n"
            "    - source: vendor/brand\n"
            "      mountPath: /assets/vendor/brand/",
        ),
        encoding="utf-8",
    )
    (workspace_root / "site/root-pages").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/root-pages/index.md").write_text(
        "site page\n",
        encoding="utf-8",
    )
    (workspace_root / "site/root-assets").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/root-assets/site.css").write_text(
        "body {}\n",
        encoding="utf-8",
    )
    (workspace_root / "vendor/brand").mkdir(parents=True, exist_ok=True)
    (workspace_root / "vendor/brand/logo.svg").write_text("<svg/>", encoding="utf-8")


def _stage_snapshot(stage_root: Path) -> dict[str, object]:
    snapshot: dict[str, object] = {}
    for file_path in sorted(path for path in stage_root.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(stage_root).as_posix()
        if file_path.suffix == ".json":
            snapshot[relative_path] = _normalized_json(
                json.loads(file_path.read_text(encoding="utf-8")),
            )
        else:
            snapshot[relative_path] = file_path.read_bytes()
    return snapshot


def _normalized_json(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalized_json(item) for key, item in value.items() if key != "generatedAt"}
    if isinstance(value, list):
        return [_normalized_json(item) for item in value]
    return value


def _work_layout(workspace_root: Path) -> WorkRootLayout:
    work_root = workspace_root / "work"
    next_stage_root = workspace_root / "next-stage"
    content_root = next_stage_root / "content"
    static_root = next_stage_root / "static"
    data_root = next_stage_root / "data"
    fragments_root = work_root / "fragments"
    units_root = work_root / "units"
    for path in (
        work_root,
        next_stage_root,
        content_root,
        static_root,
        data_root,
        fragments_root,
        units_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return WorkRootLayout(
        work_root=work_root,
        next_stage_root=next_stage_root,
        content_root=content_root,
        static_root=static_root,
        data_root=data_root,
        fragments_root=fragments_root,
        units_root=units_root,
    )