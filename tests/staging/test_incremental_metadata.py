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

"""Tests for retained stage incremental metadata helpers."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from apache_buildish_site_pipeline.models.enums import StageCommand
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    StageDataFiles,
    StageManifestV1,
    StageRoots,
)
from apache_buildish_site_pipeline.staging.incremental_metadata import (
    PersistedUnitContributionsV1,
    build_aggregate_dependency_map,
    build_output_ownership_map,
    load_retained_stage_incremental_state,
)
from apache_buildish_site_pipeline.staging.ownership import OwnedUnit, OwnedUnitKind


class IncrementalMetadataTests(unittest.TestCase):
    def test_build_output_ownership_map_includes_sorted_unit_and_coordinator_claims(self) -> None:
        ownership = build_output_ownership_map(
            units=(
                self._owned_unit("unit-b", "owner-b", content="content/b"),
                self._owned_unit("unit-a", "owner-a", static="static/a"),
            ),
            data_files=self._data_files(),
        )

        self.assertEqual(
            [claim.stage_relative_path for claim in ownership.claims],
            [
                "content/b",
                "data/aggregate-dependencies.json",
                "data/artifacts.json",
                "data/components.json",
                "data/output-ownership.json",
                "data/redirects.json",
                "data/routes.json",
                "data/unit-contributions.json",
                "manifest.json",
                "static/a",
            ],
        )

    def test_build_aggregate_dependency_map_sorts_dependent_unit_ids(self) -> None:
        dependency_map = build_aggregate_dependency_map(
            units=(
                self._owned_unit("unit-z", "owner-z"),
                self._owned_unit("unit-a", "owner-a"),
            ),
            data_files=self._data_files(),
        )

        self.assertEqual(
            [entry.stage_relative_path for entry in dependency_map.entries],
            [
                "data/components.json",
                "data/artifacts.json",
                "data/routes.json",
                "data/redirects.json",
            ],
        )
        self.assertEqual(
            dependency_map.entries[0].dependent_unit_ids,
            ("unit-a", "unit-z"),
        )

    def test_load_retained_stage_incremental_state_returns_none_when_metadata_not_configured(self) -> None:
        state = load_retained_stage_incremental_state(
            stage_root=Path("/stage"),
            manifest=self._manifest(
                self._data_files(unit_contributions=None, output_ownership=None)
            ),
        )

        self.assertIsNone(state)

    def test_load_retained_stage_incremental_state_rejects_symlinked_metadata_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            stage_root = Path(temp_dir)
            data_dir = stage_root / "data"
            data_dir.mkdir()
            self._write_metadata_files(stage_root)
            link_target = data_dir / "unit-contributions.actual.json"
            link_target.write_text(
                PersistedUnitContributionsV1().model_dump_json(indent=2),
                encoding="utf-8",
            )
            (data_dir / "unit-contributions.json").unlink()
            (data_dir / "unit-contributions.json").symlink_to(link_target)

            state = load_retained_stage_incremental_state(
                stage_root=stage_root,
                manifest=self._manifest(self._data_files()),
            )

        self.assertIsNone(state)

    def test_load_retained_stage_incremental_state_reads_trusted_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            stage_root = Path(temp_dir)
            (stage_root / "data").mkdir()
            self._write_metadata_files(stage_root)

            state = load_retained_stage_incremental_state(
                stage_root=stage_root,
                manifest=self._manifest(self._data_files()),
            )

        self.assertIsNotNone(state)
        self.assertEqual(state.output_ownership.claims[0].owner_id, "coordinator")
        self.assertEqual(state.aggregate_dependencies.entries[0].stage_relative_path, "data/components.json")

    @staticmethod
    def _owned_unit(
        unit_id: str,
        owner_id: str,
        *,
        content: str | None = None,
        static: str | None = None,
    ) -> OwnedUnit:
        return OwnedUnit(
            unit_id=unit_id,
            owner_id=owner_id,
            kind=OwnedUnitKind.COMPONENT,
            content_stage_roots=((Path(content),) if content else ()),
            static_stage_roots=((Path(static),) if static else ()),
        )

    @staticmethod
    def _data_files(
        *,
        unit_contributions: str | None = "data/unit-contributions.json",
        output_ownership: str | None = "data/output-ownership.json",
        aggregate_dependencies: str | None = "data/aggregate-dependencies.json",
    ) -> StageDataFiles:
        return StageDataFiles(
            components="data/components.json",
            artifacts="data/artifacts.json",
            routes="data/routes.json",
            redirects="data/redirects.json",
            unit_contributions=unit_contributions,
            output_ownership=output_ownership,
            aggregate_dependencies=aggregate_dependencies,
        )

    @classmethod
    def _manifest(cls, data_files: StageDataFiles) -> StageManifestV1:
        return StageManifestV1(
            schema_version=1,
            stage_layout_version=1,
            generated_at=datetime(2026, 4, 5, tzinfo=UTC),
            command=StageCommand.BUILD,
            front_matter_format="yaml",
            aggregate_format="json",
            roots=StageRoots(content="content", static="static", data="data"),
            data_files=data_files,
        )

    @classmethod
    def _write_metadata_files(cls, stage_root: Path) -> None:
        data_dir = stage_root / "data"
        (data_dir / "unit-contributions.json").write_text(
            PersistedUnitContributionsV1().model_dump_json(indent=2),
            encoding="utf-8",
        )
        (data_dir / "output-ownership.json").write_text(
            build_output_ownership_map(units=(), data_files=cls._data_files()).model_dump_json(indent=2),
            encoding="utf-8",
        )
        (data_dir / "aggregate-dependencies.json").write_text(
            build_aggregate_dependency_map(units=(), data_files=cls._data_files()).model_dump_json(indent=2),
            encoding="utf-8",
        )
