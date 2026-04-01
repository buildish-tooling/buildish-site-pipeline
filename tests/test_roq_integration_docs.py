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

"""Protect the renderer boundary described by the Roq integration guide."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from buildish_site_pipeline.cli import _run
from examples.roq.sync_stage import AdapterError, synchronize_stage
from tests.support.workspace import _cwd


_ROQ_STAGE_MAPPINGS = (
    ("data", "data"),
    ("static", "public"),
)


class RoqIntegrationDocsTests(unittest.TestCase):
    """Keep the copyable Roq contract aligned with Site Pipeline output."""

    def test_renderer_index_links_to_roq_with_a_pretty_route(self) -> None:
        index_text = Path("site/pages/how-to/_index.md").read_text(encoding="utf-8")

        self.assertIn("[integrate with Roq](integrate-with-roq/)", index_text)
        self.assertNotIn("integrate-with-roq.md", index_text)

    def test_guide_maps_each_stage_root_to_the_correct_roq_root(self) -> None:
        guide_text = Path("site/pages/how-to/integrate-with-roq.md").read_text(
            encoding="utf-8"
        )

        for expected_mapping in (
            "site/.stage/data/ site/roq/data/",
            "site/.stage/static/ site/roq/public/",
        ):
            self.assertIn(expected_mapping, guide_text)

        self.assertIn("content/site/", guide_text)
        self.assertIn("`_index.<extension>` page to `index.<extension>`", guide_text)
        self.assertIn("site.slugify-files=false", guide_text)
        self.assertIn("python3 site/roq/sync_stage.py site/.stage site/roq", guide_text)
        self.assertIn("examples/roq/sync_stage.py", guide_text)
        self.assertIn("Do not synchronize `manifest.json` into `data/`", guide_text)
        self.assertNotIn("site/.stage/static/ site/roq/static/", guide_text)
        self.assertNotIn("`sync-stage` is a placeholder", guide_text)

    def test_guide_uses_current_roq_and_watch_commands(self) -> None:
        guide_text = Path("site/pages/how-to/integrate-with-roq.md").read_text(
            encoding="utf-8"
        )

        for command in (
            "roq start",
            "roq generate",
            "--unstable-events jsonl",
            "--unstable-events-output",
        ):
            self.assertIn(command, guide_text)

        self.assertIn("does not download or execute Roq", guide_text)
        self.assertIn("build the checked-in smoke workspace", guide_text)

    def test_smoke_fixture_pins_the_roq_runtime_contract(self) -> None:
        fixture_root = Path("tests/fixtures/roq-smoke")
        pom_text = (fixture_root / "pom.xml").read_text(encoding="utf-8")

        self.assertIn("<maven.compiler.release>21</maven.compiler.release>", pom_text)
        self.assertIn("<quarkus.version>3.35.1</quarkus.version>", pom_text)
        self.assertIn("<roq.version>2.1.6</roq.version>", pom_text)
        self.assertTrue(Path("examples/roq/sync_stage.py").is_file())
        for relative_path in (
            "content/index.md",
            "content/components/site-pipeline/index.md",
            "data/components.json",
            "public/site/assets/site-pipeline-smoke.txt",
            "templates/layouts/smoke.html",
            "workspace/site/catalog.yaml",
            "workspace/site/pages/_index.md",
            "workspace/site/assets/assets/site-pipeline-smoke.txt",
            "workspace/components/site-pipeline/site/component.yaml",
            "workspace/components/site-pipeline/site/pages/_index.md",
        ):
            self.assertTrue((fixture_root / relative_path).is_file(), relative_path)

    def test_real_pipeline_stage_synchronizes_into_roq_generated_roots(self) -> None:
        fixture_root = Path("tests/fixtures/roq-smoke")
        with tempfile.TemporaryDirectory() as tempdir:
            roq_root = Path(tempdir) / "roq-smoke"
            shutil.copytree(fixture_root, roq_root)
            workspace_root = roq_root / "workspace"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "build",
                        "--workspace-root",
                        ".",
                        "--catalog",
                        "site/catalog.yaml",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

            self.assertEqual(0, exit_code, stdout.getvalue() + stderr.getvalue())
            stage_root = workspace_root / "site/.stage"
            self.assertTrue((stage_root / "manifest.json").is_file())

            for destination_name in ("content", "data", "public"):
                stale_path = roq_root / destination_name / "stale-from-prior-stage.txt"
                stale_path.parent.mkdir(parents=True, exist_ok=True)
                stale_path.write_text("stale\n", encoding="utf-8")

            synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            for source_name, destination_name in _ROQ_STAGE_MAPPINGS:
                self.assertEqual(
                    _tree_contents(stage_root / source_name),
                    _tree_contents(roq_root / destination_name),
                )
                self.assertFalse(
                    (
                        roq_root / destination_name / "stale-from-prior-stage.txt"
                    ).exists()
                )

            self.assertEqual(
                (stage_root / "content/site/_index.md").read_bytes(),
                (roq_root / "content/index.md").read_bytes(),
            )
            component_page_path = roq_root / "content/components/site-pipeline/index.md"
            self.assertEqual(
                (
                    stage_root / "content/components/site-pipeline/_index.md"
                ).read_bytes(),
                component_page_path.read_bytes(),
            )
            self.assertFalse((roq_root / "content/site").exists())
            self.assertEqual([], list((roq_root / "content").rglob("_index.*")))

            component_page = component_page_path.read_text(encoding="utf-8")
            self.assertIn("layout: smoke", component_page)
            self.assertIn("slug: site-pipeline", component_page)
            self.assertIn("path: /components/site-pipeline", component_page)
            self.assertIn("items.asJsonObjects.first.slug", component_page)

            components = json.loads(
                (roq_root / "data/components.json").read_text(encoding="utf-8")
            )
            self.assertEqual("site-pipeline", components["items"][0]["slug"])
            self.assertFalse((roq_root / "data/manifest.json").exists())
            self.assertEqual(
                (
                    stage_root / "static/site/assets/site-pipeline-smoke.txt"
                ).read_bytes(),
                (roq_root / "public/site/assets/site-pipeline-smoke.txt").read_bytes(),
            )

    def test_roq_content_adaptation_rejects_route_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            roq_root = Path(tempdir) / "roq"
            (stage_root / "content/site").mkdir(parents=True)
            (stage_root / "content/example.md").write_text(
                "component\n", encoding="utf-8"
            )
            (stage_root / "content/site/example.md").write_text(
                "site\n", encoding="utf-8"
            )
            for source_name, _ in _ROQ_STAGE_MAPPINGS:
                (stage_root / source_name).mkdir()
            _write_stage_manifest(stage_root)
            roq_root.mkdir()

            with self.assertRaisesRegex(AdapterError, "content collision"):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            self.assertEqual([], list(roq_root.iterdir()))

    def test_roq_synchronization_requires_a_completed_plain_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            roq_root = Path(tempdir) / "roq"
            stage_root.mkdir()

            roq_root.mkdir()
            with self.assertRaisesRegex(AdapterError, "completed stage manifest"):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            _write_stage_manifest(stage_root)
            for source_name in ("content", "data", "static"):
                (stage_root / source_name).mkdir()
            (stage_root / "content/index.md").symlink_to(stage_root / "manifest.json")

            with self.assertRaisesRegex(AdapterError, "must not contain symlinks"):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            (stage_root / "content/index.md").unlink()
            (roq_root / "content").symlink_to(
                stage_root / "content", target_is_directory=True
            )

            with self.assertRaisesRegex(AdapterError, "generated root"):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)


def _write_stage_manifest(stage_root: Path) -> None:
    (stage_root / "manifest.json").write_text(
        json.dumps(
            {
                "stageLayoutVersion": 1,
                "roots": {
                    "content": "content",
                    "data": "data",
                    "static": "static",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _tree_contents(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(
            candidate for candidate in root.rglob("*") if candidate.is_file()
        )
    }


if __name__ == "__main__":
    unittest.main()
