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

from pathlib import Path
import shutil
import tempfile
import unittest

from buildish_site_pipeline.legal.container_inventory import (
    bundled_container_image_refs,
    collect_container_base_image_entries,
)


class ContainerImageLegalFilesTests(unittest.TestCase):
    def test_containerfile_copies_build_inputs_before_install(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        copy_root_inputs = containerfile_text.index(
            "COPY README.md pyproject.toml uv.lock main.py dist-release-legal/LICENSE dist-release-legal/NOTICE ./"
        )
        copy_src = containerfile_text.index("COPY src ./src")
        copy_tools = containerfile_text.index("COPY tools/helpers ./tools/helpers")
        apt_install_step = containerfile_text.index("apt-get install -y --no-install-recommends ca-certificates;")
        install_step = containerfile_text.index("uv sync --frozen --no-dev --no-editable;")

        self.assertLess(copy_root_inputs, install_step)
        self.assertLess(copy_src, install_step)
        self.assertLess(copy_tools, install_step)
        self.assertLess(apt_install_step, install_step)

    def test_containerfile_derives_build_time_release_legal_layout_from_root_files(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("mkdir -p dist-release-legal;", containerfile_text)
        self.assertIn("cp LICENSE NOTICE dist-release-legal/;", containerfile_text)

    def test_containerfile_removes_build_only_inputs_after_install(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("rm -rf tools dist-release-legal pyproject.toml uv.lock", containerfile_text)
        self.assertNotIn("rm -f /usr/local/bin/uv /usr/local/bin/uvx", containerfile_text)

    def test_containerfile_copies_final_release_legal_files(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "COPY README.md pyproject.toml uv.lock main.py dist-release-legal/LICENSE dist-release-legal/NOTICE ./",
            containerfile_text,
        )
        self.assertIn("COPY --from=uvbin /uv /uvx /usr/local/bin/", containerfile_text)

    def test_containerfile_runs_as_dedicated_non_root_runtime_user(self) -> None:
        containerfile_text = Path("tools/site-pipeline-image/Containerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("groupadd --system --gid 10001 site-pipeline", containerfile_text)
        self.assertIn(
            "useradd --system --uid 10001 --gid site-pipeline --create-home --home-dir /home/site-pipeline site-pipeline",
            containerfile_text,
        )
        self.assertIn(
            "chown -R site-pipeline:site-pipeline /home/site-pipeline /workspace",
            containerfile_text,
        )
        self.assertIn("HOME=/home/site-pipeline", containerfile_text)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", containerfile_text)
        self.assertIn("WORKDIR /workspace", containerfile_text)
        self.assertIn("USER site-pipeline", containerfile_text)

    def test_final_release_legal_files_exist(self) -> None:
        self.assertTrue(Path("dist-release-legal/LICENSE").is_file())
        self.assertTrue(Path("dist-release-legal/NOTICE").is_file())

    def test_curated_base_image_legal_manifest_matches_containerfile(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        containerfile = project_root / "tools/site-pipeline-image/Containerfile"

        image_refs = bundled_container_image_refs(containerfile)
        entries = collect_container_base_image_entries(project_root)

        self.assertEqual(
            tuple(entry.source_reference for entry in entries),
            image_refs,
        )
        self.assertEqual(
            {entry.name for entry in entries},
            {"python", "uv"},
        )
        self.assertTrue(all(entry.license_files for entry in entries))


class ContainerImageUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        image_dir = Path("tools/site-pipeline-image")
        shutil.copytree(image_dir / "legal", self.root / image_dir / "legal")
        shutil.copyfile("LICENSE", self.root / "LICENSE")
        self.containerfile = self.root / image_dir / "Containerfile"
        self.containerfile.write_text(
            f"FROM ghcr.io/astral-sh/uv:0.12.1@sha256:{'a' * 64} AS uvbin\n"
            f"FROM docker.io/library/python:3.13-bookworm@sha256:{'b' * 64}\n"
            "COPY --from=uvbin /uv /usr/local/bin/uv\n",
            encoding="utf-8",
        )

    def test_digest_and_uv_updates_need_only_containerfile_changes(self) -> None:
        before = collect_container_base_image_entries(self.root)
        text = self.containerfile.read_text(encoding="utf-8")
        text = text.replace("0.12.1", "0.13.5").replace("b" * 64, "c" * 64)
        self.containerfile.write_text(text, encoding="utf-8")

        after = collect_container_base_image_entries(self.root)

        self.assertEqual([entry.version for entry in after], ["0.13.5", "3.13-bookworm"])
        self.assertEqual(after[1].source_reference, f"docker.io/library/python:3.13-bookworm@sha256:{'c' * 64}")
        self.assertEqual(
            [entry.captured_legal_files for entry in before],
            [entry.captured_legal_files for entry in after],
        )

    def test_unsupported_python_tags_are_rejected(self) -> None:
        original = self.containerfile.read_text(encoding="utf-8")
        for tag in ("3.15-bookworm", "3.13-alpine", "3.13-bookworm-extra"):
            with self.subTest(tag=tag):
                self.containerfile.write_text(original.replace("3.13-bookworm", tag), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "outside.*supported tags"):
                    collect_container_base_image_entries(self.root)

    def test_unknown_image_repository_is_rejected(self) -> None:
        text = self.containerfile.read_text(encoding="utf-8")
        self.containerfile.write_text(text.replace("ghcr.io/astral-sh/uv", "example.invalid/uv"), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "no curated.*metadata"):
            collect_container_base_image_entries(self.root)

    def test_unpinned_image_is_rejected(self) -> None:
        text = self.containerfile.read_text(encoding="utf-8")
        self.containerfile.write_text(text.replace(f"@sha256:{'a' * 64}", ""), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "SHA-256-pinned"):
            collect_container_base_image_entries(self.root)

    def test_missing_curated_license_is_rejected(self) -> None:
        (self.root / "tools/site-pipeline-image/legal/base-images/uv/LICENSE-MIT").unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing curated license"):
            collect_container_base_image_entries(self.root)


if __name__ == "__main__":
    unittest.main()
