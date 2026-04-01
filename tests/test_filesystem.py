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

"""Tests for low-level filesystem safety and staging helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.filesystem import copy_tree_without_symlinks
from apache_buildish_site_pipeline.filesystem import reset_output_directory
from apache_buildish_site_pipeline.filesystem import safe_relative_path
from apache_buildish_site_pipeline.filesystem import safe_repo_path
from apache_buildish_site_pipeline.filesystem import safe_workspace_checkout_path
from apache_buildish_site_pipeline.filesystem import stage_vendor_assets

from tests.test_support import write_files
from tests.test_support import write_text


class PathSafetyTest(unittest.TestCase):
    def test_safe_repo_path_resolves_workspace_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            repo_root.mkdir()

            resolved = safe_repo_path(repo_root, "mammoth-cache")

            self.assertEqual((Path(temp_dir) / "mammoth-cache").resolve(), resolved)

    def test_safe_workspace_checkout_path_rejects_escaping_workspace_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            repo_root.mkdir()

            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                safe_workspace_checkout_path(repo_root, "../../outside", "checkoutDir")

    def test_safe_workspace_checkout_path_accepts_repo_relative_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            repo_root.mkdir()

            resolved = safe_workspace_checkout_path(
                repo_root,
                "../src/mammoth-cache",
                "checkoutDir",
                relative_to_repo_root=True,
            )

            self.assertEqual((Path(temp_dir) / "src" / "mammoth-cache").resolve(), resolved)

    def test_safe_relative_path_rejects_paths_that_escape_the_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir) / "site"
            base.mkdir()

            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                safe_relative_path(base, "../secrets.txt", "docsRoot")


class CopyAndResetHelpersTest(unittest.TestCase):
    def test_copy_tree_without_symlinks_skips_hidden_entries_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            destination = root / "destination"
            write_files(
                source,
                {
                    "regular.txt": "regular\n",
                    ".hidden.txt": "hidden\n",
                    "nested/data.md": "nested\n",
                    ".secret/ignored.txt": "ignored\n",
                },
            )
            (source / "link.txt").symlink_to(source / "regular.txt")
            (source / "linked-dir").symlink_to(source / "nested", target_is_directory=True)

            copied = copy_tree_without_symlinks(source, destination)

            self.assertEqual({Path("regular.txt"), Path("nested/data.md")}, set(copied))
            self.assertTrue((destination / "regular.txt").is_file())
            self.assertTrue((destination / "nested" / "data.md").is_file())
            self.assertFalse((destination / ".hidden.txt").exists())
            self.assertFalse((destination / ".secret").exists())
            self.assertFalse((destination / "link.txt").exists())
            self.assertFalse((destination / "linked-dir").exists())

    def test_reset_output_directory_replaces_symlink_root_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            external = root / "external-stage"
            output = root / "stage"
            write_text(external / "keep.txt", "keep me\n")
            output.symlink_to(external, target_is_directory=True)

            reset_output_directory(output)

            self.assertTrue(output.is_dir())
            self.assertFalse(output.is_symlink())
            self.assertEqual([], list(output.iterdir()))
            self.assertTrue((external / "keep.txt").is_file())


class VendorAssetsTest(unittest.TestCase):
    def test_stage_vendor_assets_copies_only_existing_vendor_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            site_root = root / "site"
            stage_root = root / "stage"
            write_text(
                site_root / "node_modules" / "jquery" / "dist" / "jquery.min.js",
                "/*! jquery */\n",
            )

            stage_vendor_assets(site_root, stage_root)

            self.assertTrue((stage_root / "static" / "js" / "vendor" / "jquery.min.js").is_file())
            self.assertFalse((stage_root / "static" / "js" / "vendor" / "mermaid.min.js").exists())
            self.assertFalse((stage_root / "static" / "js" / "vendor" / "lunr.min.js").exists())