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
from unittest.mock import patch

from apache_buildish_site_pipeline.filesystem import load_component_metadata
from apache_buildish_site_pipeline.filesystem import load_components_local_overrides
from apache_buildish_site_pipeline.filesystem import copy_tree_without_symlinks
from apache_buildish_site_pipeline.filesystem import read_text_if_exists
from apache_buildish_site_pipeline.filesystem import resolve_component_repo_path
from apache_buildish_site_pipeline.filesystem import resolve_vendor_asset_source
from apache_buildish_site_pipeline.filesystem import reset_output_directory
from apache_buildish_site_pipeline.filesystem import safe_relative_path
from apache_buildish_site_pipeline.filesystem import safe_repo_path
from apache_buildish_site_pipeline.filesystem import safe_workspace_checkout_path
from apache_buildish_site_pipeline.filesystem import stage_vendor_assets
from apache_buildish_site_pipeline.filesystem import watchable_existing_path
from apache_buildish_site_pipeline.models import CatalogComponent

from tests.test_support import dump_yaml
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

    def test_safe_workspace_checkout_path_accepts_absolute_workspace_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            repo_root.mkdir()
            checkout_path = Path(temp_dir) / "mammoth-cache"
            checkout_path.mkdir()

            resolved = safe_workspace_checkout_path(
                repo_root,
                str(checkout_path.resolve()),
                "checkoutDir",
            )

            self.assertEqual(checkout_path.resolve(), resolved)

    def test_safe_relative_path_rejects_paths_that_escape_the_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir) / "site"
            base.mkdir()

            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                safe_relative_path(base, "../secrets.txt", "docsRoot")

    def test_safe_relative_path_returns_none_for_empty_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir) / "site"
            base.mkdir()

            self.assertIsNone(safe_relative_path(base, "", "docsRoot"))


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

    def test_reset_output_directory_removes_nested_files_and_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "stage"
            write_files(
                output,
                {
                    "nested/guide.md": "guide\n",
                    "top.txt": "top\n",
                },
            )

            reset_output_directory(output)

            self.assertTrue(output.is_dir())
            self.assertEqual([], list(output.iterdir()))


class VendorAssetsTest(unittest.TestCase):
    def test_resolve_vendor_asset_source_uses_node_modules_override_directory(self) -> None:
        site_root = Path("/workspace/site")
        source_relative = Path("node_modules/jquery/dist/jquery.min.js")

        with patch.dict("os.environ", {"NODE_MODULES_DIR": "/opt/node_modules"}, clear=False):
            resolved = resolve_vendor_asset_source(site_root, source_relative)

        self.assertEqual(Path("/opt/node_modules/jquery/dist/jquery.min.js"), resolved)

    def test_resolve_vendor_asset_source_falls_back_for_non_node_modules_paths(self) -> None:
        site_root = Path("/workspace/site")
        source_relative = Path("vendor/jquery.min.js")

        with patch.dict("os.environ", {"NODE_MODULES_DIR": "/opt/node_modules"}, clear=False):
            resolved = resolve_vendor_asset_source(site_root, source_relative)

        self.assertEqual(site_root / source_relative, resolved)

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


class ComponentFilesystemHelpersTest(unittest.TestCase):
    def test_load_component_metadata_returns_defaults_when_metadata_path_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata, metadata_path = load_component_metadata(
                Path(temp_dir),
                None,
                "mammoth-cache",
            )

        self.assertIsNone(metadata_path)
        self.assertIsNone(metadata.component.display_name)

    def test_load_component_metadata_returns_defaults_when_metadata_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata, metadata_path = load_component_metadata(
                Path(temp_dir),
                "site/component.yaml",
                "mammoth-cache",
            )

        self.assertIsNone(metadata_path)
        self.assertIsNone(metadata.component.display_name)

    def test_load_component_metadata_rejects_slug_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            dump_yaml(
                repo_path / "site" / "component.yaml",
                {
                    "schemaVersion": 1,
                    "component": {"slug": "other-cache", "displayName": "Other"},
                },
            )

            with self.assertRaisesRegex(ValueError, "slug mismatch"):
                load_component_metadata(repo_path, "site/component.yaml", "mammoth-cache")

    def test_load_components_local_overrides_reads_workspace_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir) / "site"
            dump_yaml(
                site_root / "components.local.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {
                        "components": {
                            "mammoth-cache": {"checkoutDir": "../src/mammoth-cache"}
                        }
                    },
                },
            )

            overrides = load_components_local_overrides(site_root)

        self.assertEqual(
            "../src/mammoth-cache",
            overrides.workspace.components["mammoth-cache"].checkout_dir,
        )

    def test_resolve_component_repo_path_prefers_local_override_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            site_root = repo_root / "site"
            dump_yaml(
                site_root / "components.local.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {
                        "components": {
                            "mammoth-cache": {"checkoutDir": "../src/mammoth-cache"}
                        }
                    },
                },
            )
            component = CatalogComponent(slug="mammoth-cache", local_dir="../fallback-cache")

            resolved = resolve_component_repo_path(
                repo_root,
                component,
                load_components_local_overrides(site_root),
            )

        self.assertEqual(
            (Path(temp_dir) / "src" / "mammoth-cache").resolve(),
            resolved,
        )

    def test_resolve_component_repo_path_uses_component_local_dir_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "workspace" / "consumer"
            repo_root.mkdir(parents=True)
            component = CatalogComponent(slug="mammoth-cache", local_dir="mammoth-cache")

            resolved = resolve_component_repo_path(repo_root, component)

        self.assertEqual((Path(temp_dir) / "workspace" / "mammoth-cache").resolve(), resolved)

    def test_watchable_existing_path_returns_nearest_existing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "docs"
            existing.mkdir()

            watched = watchable_existing_path(existing / "future" / "guide.md", root)

        self.assertEqual(existing.resolve(), watched)

    def test_watchable_existing_path_returns_fallback_even_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fallback = root / "docs"

            watched = watchable_existing_path(fallback / "future" / "guide.md", fallback)

        self.assertEqual(fallback.resolve(), watched)

    def test_read_text_if_exists_returns_empty_string_for_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.txt"

            self.assertEqual("", read_text_if_exists(None))
            self.assertEqual("", read_text_if_exists(missing))

    def test_read_text_if_exists_reads_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "note.txt"
            file_path.write_text("hello\n", encoding="utf-8")

            self.assertEqual("hello\n", read_text_if_exists(file_path))