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

"""Exercise the copyable Roq stage synchronization example."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from examples.roq.sync_stage import AdapterError, synchronize_stage


class RoqSyncExampleTests(unittest.TestCase):
    """Protect safe replacement and manifest-driven discovery behavior."""

    def test_manifest_root_names_are_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "stage"
            roq_root = root / "roq"
            _create_stage(
                stage_root,
                roots={"content": "pages", "data": "metadata", "static": "assets"},
            )
            roq_root.mkdir()
            (stage_root / "pages/site/_index.md").parent.mkdir(parents=True)
            (stage_root / "pages/site/_index.md").write_bytes(b"site page\n")
            (stage_root / "pages/_index.txt").write_bytes(b"ordinary attachment\n")
            (stage_root / "metadata/components.json").write_bytes(b'{"items": []}\n')
            (stage_root / "assets/example.bin").write_bytes(b"\x00asset\xff")

            synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            self.assertEqual(
                b"site page\n", (roq_root / "content/index.md").read_bytes()
            )
            self.assertEqual(
                b"ordinary attachment\n",
                (roq_root / "content/_index.txt").read_bytes(),
            )
            self.assertEqual(
                b'{"items": []}\n',
                (roq_root / "data/components.json").read_bytes(),
            )
            self.assertEqual(
                b"\x00asset\xff", (roq_root / "public/example.bin").read_bytes()
            )

    def test_manifest_rejects_escaping_and_duplicate_roots(self) -> None:
        for roots, expected_message in (
            (
                {"content": "../pages", "data": "data", "static": "static"},
                "not stage-relative",
            ),
            (
                {"content": "content", "data": "content", "static": "static"},
                "must be distinct",
            ),
        ):
            with self.subTest(roots=roots), tempfile.TemporaryDirectory() as tempdir:
                root = Path(tempdir)
                stage_root = root / "stage"
                roq_root = root / "roq"
                stage_root.mkdir()
                roq_root.mkdir()
                _write_manifest(stage_root, roots=roots)

                with self.assertRaisesRegex(AdapterError, expected_message):
                    synchronize_stage(stage_root=stage_root, roq_root=roq_root)

                self.assertEqual([], list(roq_root.iterdir()))

    def test_unknown_layout_and_symlinked_root_components_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "stage"
            roq_root = root / "roq"
            stage_root.mkdir()
            roq_root.mkdir()
            (stage_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "stageLayoutVersion": 2,
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

            with self.assertRaisesRegex(AdapterError, "only stage layout version 1"):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            outside_root = root / "outside"
            (outside_root / "content").mkdir(parents=True)
            (stage_root / "linked").symlink_to(outside_root, target_is_directory=True)
            (stage_root / "data").mkdir()
            (stage_root / "static").mkdir()
            _write_manifest(
                stage_root,
                roots={"content": "linked/content", "data": "data", "static": "static"},
            )

            with self.assertRaisesRegex(
                AdapterError, "paths must not contain symlinks"
            ):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            self.assertEqual([], list(roq_root.iterdir()))

    def test_case_insensitive_adapted_collision_preserves_existing_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "stage"
            roq_root = root / "roq"
            _create_stage(stage_root)
            roq_root.mkdir()
            (stage_root / "content/guide.md").write_bytes(b"component\n")
            (stage_root / "content/site/Guide.md").parent.mkdir(parents=True)
            (stage_root / "content/site/Guide.md").write_bytes(b"site\n")
            _seed_old_roq_roots(roq_root)

            with self.assertRaisesRegex(AdapterError, "content collision"):
                synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            _assert_old_roq_roots(self, roq_root)

    def test_publish_failure_rolls_back_every_replaced_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "stage"
            roq_root = root / "roq"
            _create_stage(stage_root)
            roq_root.mkdir()
            (stage_root / "content/index.md").write_bytes(b"new content\n")
            (stage_root / "data/new.json").write_bytes(b"{}\n")
            (stage_root / "static/new.txt").write_bytes(b"new asset\n")
            _seed_old_roq_roots(roq_root)

            original_replace = Path.replace

            def fail_prepared_data(source: Path, target: Path) -> Path:
                if source.name == "data" and source.parent.name.startswith(
                    ".site-pipeline-sync-"
                ):
                    raise OSError("injected publication failure")
                return original_replace(source, target)

            with patch.object(
                Path, "replace", autospec=True, side_effect=fail_prepared_data
            ):
                with self.assertRaisesRegex(AdapterError, "could not replace"):
                    synchronize_stage(stage_root=stage_root, roq_root=roq_root)

            _assert_old_roq_roots(self, roq_root)
            self.assertEqual(
                [],
                list(roq_root.glob(".site-pipeline-sync-*")),
                "temporary publication roots must be removed",
            )

    def test_command_reports_adapter_errors_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "incomplete-stage"
            roq_root = root / "roq"
            stage_root.mkdir()
            roq_root.mkdir()

            completed = subprocess.run(  # noqa: S603
                [
                    sys.executable,
                    "examples/roq/sync_stage.py",
                    str(stage_root),
                    str(roq_root),
                ],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(1, completed.returncode)
            self.assertIn("completed stage manifest", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertEqual("", completed.stdout)


def _create_stage(
    stage_root: Path,
    *,
    roots: dict[str, str] | None = None,
) -> None:
    selected_roots = roots or {
        "content": "content",
        "data": "data",
        "static": "static",
    }
    stage_root.mkdir()
    for relative_path in selected_roots.values():
        (stage_root / relative_path).mkdir(parents=True, exist_ok=True)
    _write_manifest(stage_root, roots=selected_roots)


def _write_manifest(stage_root: Path, *, roots: dict[str, str]) -> None:
    (stage_root / "manifest.json").write_text(
        json.dumps({"stageLayoutVersion": 1, "roots": roots}) + "\n",
        encoding="utf-8",
    )


def _seed_old_roq_roots(roq_root: Path) -> None:
    for root_name in ("content", "data", "public"):
        generated_root = roq_root / root_name
        generated_root.mkdir()
        (generated_root / "old.txt").write_bytes(f"old {root_name}\n".encode())


def _assert_old_roq_roots(test: unittest.TestCase, roq_root: Path) -> None:
    for root_name in ("content", "data", "public"):
        test.assertEqual(
            f"old {root_name}\n".encode(),
            (roq_root / root_name / "old.txt").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
