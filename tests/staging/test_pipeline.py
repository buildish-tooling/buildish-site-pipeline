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

from __future__ import annotations

import io
import json
import unittest
from pathlib import Path

import frontmatter

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError
from apache_buildish_site_pipeline.cli import _run
from apache_buildish_site_pipeline.commands.shared import load_workspace_inputs
from apache_buildish_site_pipeline.models.enums import PlanningTarget
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.ownership import OwnedUnit, OwnedUnitKind, _validate_output_ownership, build_owned_units
from tests.support.workspace import _cwd, _workspace


class StagingPipelineTests(unittest.TestCase):
    def test_build_owned_units_group_contexts_under_component_owner(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            loaded_inputs = load_workspace_inputs(workspace_root)
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=loaded_inputs.catalog,
                provider_snapshot=loaded_inputs.provider_snapshot,
                workspace_root=workspace_root,
                component_documents=loaded_inputs.component_documents,
                stage_root=workspace_root / "site/.stage",
                work_root=workspace_root / ".buildish/work",
            )

        self.assertIsNotNone(planning.build_plan_candidate)
        units = build_owned_units(planning.build_plan_candidate)
        self.assertEqual([unit.kind for unit in units], [OwnedUnitKind.COMPONENT])
        component_unit = units[0]
        self.assertEqual(component_unit.owner_id, "component:spark")
        self.assertEqual(component_unit.component_slug, "spark")
        self.assertEqual([context.context.kind.value for context in component_unit.contexts], ["development", "lineHead", "released"])
        self.assertEqual(
            [context.content_stage_root.as_posix() for context in component_unit.contexts],
            [
                "content/components/spark/contexts/development",
                "content/components/spark/contexts/line-heads/4.0",
                "content/components/spark/contexts/releases/4.0.0",
            ],
        )

    def test_build_manifest_references_written_aggregate_files(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build", "--report-format", "json", "--report-schema-version", "1"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            manifest = json.loads((stage_root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(manifest["command"], "build")
            for key in [
                "components",
                "artifacts",
                "routes",
                "redirects",
                "providers",
                "releases",
                "refs",
                "contentIndex",
                "unitContributions",
                "outputOwnership",
                "aggregateDependencies",
            ]:
                relative_path = manifest["dataFiles"][key]
                self.assertIsNotNone(relative_path)
                self.assertTrue((stage_root / relative_path).is_file(), key)

    def test_output_ownership_rejects_case_only_stage_path_collisions(self) -> None:
        with self.assertRaises(StageIntegrityError) as raised:
            _validate_output_ownership(
                (
                    OwnedUnit(
                        unit_id="component:upper",
                        owner_id="component:upper",
                        kind=OwnedUnitKind.COMPONENT,
                        content_stage_roots=(Path("content/Docs"),),
                    ),
                    OwnedUnit(
                        unit_id="component:lower",
                        owner_id="component:lower",
                        kind=OwnedUnitKind.COMPONENT,
                        content_stage_roots=(Path("content/docs"),),
                    ),
                ),
            )

        self.assertIn("case-insensitive path collision", str(raised.exception))

    def test_build_emits_pipeline_front_matter_and_content_index(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=io.StringIO(), stderr=io.StringIO())
            stage_root = workspace_root / "site/.stage"
            release_page = frontmatter.load(stage_root / "content/components/spark/contexts/releases/4.0.0/index.md")
            content_index = json.loads((stage_root / "data/content-index.json").read_text(encoding="utf-8"))["items"]
            release_entry = next(item for item in content_index if item["pageKind"] == "release-page")

        self.assertEqual(exit_code, 0)
        self.assertEqual(release_page.metadata["pipeline"]["component"]["slug"], "spark")
        self.assertEqual(release_page.metadata["pipeline"]["page"]["kind"], "release-page")
        self.assertEqual(release_page.metadata["pipeline"]["page"]["provider"]["key"], "github")
        self.assertEqual(release_page.metadata["pipeline"]["page"]["version"]["kind"], "released")
        self.assertEqual(release_entry["path"], "/spark/development/docs/releases/4.0.0")
        self.assertEqual(release_entry["provider"], "github")
        self.assertEqual(release_entry["versionKind"], "released")


if __name__ == "__main__":
    unittest.main()
