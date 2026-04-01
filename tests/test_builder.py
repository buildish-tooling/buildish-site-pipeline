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

"""Tests for build orchestration edge cases owned by this package."""

from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import apache_buildish_site_pipeline as site_pipeline
from apache_buildish_site_pipeline.config import ResolvedWorkspacePaths
from apache_buildish_site_pipeline.models import ComponentsDataDocument
from apache_buildish_site_pipeline.models import ManifestDocument

from tests.test_support import catalog_defaults
from tests.test_support import catalog_payload
from tests.test_support import dump_yaml
from tests.test_support import text_block
from tests.test_support import write_files


def _seed_build_fixture(
    workspace: Path,
    *,
    component_files: dict[str, str],
    defaults: dict[str, object] | None = None,
) -> Path:
    repo_root = workspace / "consumer"
    dump_yaml(
        repo_root / "site" / "components.yaml",
        catalog_payload(
            {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
            defaults=defaults or catalog_defaults(),
        ),
    )
    write_files(
        repo_root,
        {
            "site/content/_index.md": text_block(
                """
                # Root

                Consumer landing page.
                """
            )
        },
    )
    write_files(workspace / "mammoth-cache", component_files)
    return repo_root


def _seed_multi_component_fixture(
    workspace: Path,
    *,
    components: tuple[dict[str, object], ...],
    component_files: dict[str, dict[str, str]],
    defaults: dict[str, object] | None = None,
) -> Path:
    repo_root = workspace / "consumer"
    dump_yaml(
        repo_root / "site" / "components.yaml",
        catalog_payload(*components, defaults=defaults or catalog_defaults()),
    )
    write_files(
        repo_root,
        {
            "site/content/_index.md": text_block(
                """
                # Root

                Consumer landing page.
                """
            )
        },
    )
    for local_dir, files in component_files.items():
        write_files(workspace / local_dir, files)
    return repo_root


def _staged_component_content_root(repo_root: Path) -> Path:
    return repo_root / "site" / ".stage" / "content" / "components" / "mammoth-cache"


def _staged_component_docs_root(repo_root: Path) -> Path:
    return _staged_component_content_root(repo_root) / "development" / "docs"


def _staged_component_assets_root(repo_root: Path) -> Path:
    return (
        repo_root
        / "site"
        / ".stage"
        / "static"
        / "components"
        / "mammoth-cache"
        / "development"
        / "assets"
    )


class BuildEdgeCaseTest(unittest.TestCase):
    def test_build_requires_component_pages_root_when_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"README.md": "workspace checkout\n"},
                defaults={"metadataFile": "site/component.yaml"},
            )

            with self.assertRaisesRegex(ValueError, "Missing required pagesRoot"):
                site_pipeline.build(repo_root)

    def test_build_rejects_missing_component_pages_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"README.md": "workspace checkout\n"},
                defaults=catalog_defaults(pagesRoot="site/missing-pages"),
            )

            with self.assertRaisesRegex(ValueError, "pagesRoot for mammoth-cache does not exist"):
                site_pipeline.build(repo_root)

    def test_build_marks_missing_components_unavailable_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = _seed_multi_component_fixture(
                workspace,
                components=(
                    {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
                    {"slug": "missing-cache", "localDir": "missing-cache"},
                ),
                component_files={
                    "mammoth-cache": {
                        "site/component.yaml": text_block(
                            """
                            schemaVersion: 1
                            component:
                              displayName: Mammoth Cache
                            """
                        ),
                        "site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n",
                        "site/docs/_index.md": "# Docs\n\nRead me first.\n",
                    }
                },
            )

            results = site_pipeline.build(repo_root)

            by_slug = {result.slug: result for result in results}
            missing = by_slug["missing-cache"]
            stage_root = repo_root / "site" / ".stage"

            self.assertFalse(missing.available)
            self.assertIsNone(missing.raw_component_index_path)
            self.assertIsNone(missing.raw_docs_root_path)
            self.assertTrue(
                any(
                    "Local repository directory is missing" in warning
                    for warning in missing.warnings
                )
            )

            manifest = ManifestDocument.from_yaml_path(stage_root / "manifest.yaml")
            manifest_missing = next(
                component
                for component in manifest.components
                if component.slug == "missing-cache"
            )
            self.assertFalse(manifest_missing.available)

            components_data = ComponentsDataDocument.from_yaml_path(
                stage_root / "data" / "components.yaml"
            )
            data_missing = components_data.components["missing-cache"]
            self.assertFalse(data_missing.available)

    def test_build_can_fail_hard_when_a_component_checkout_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_multi_component_fixture(
                Path(temp_dir),
                components=({"slug": "missing-cache", "localDir": "missing-cache"},),
                component_files={},
            )

            with self.assertRaisesRegex(
                ValueError, "Missing component checkout for 'missing-cache'"
            ):
                site_pipeline.build(repo_root, missing_components="fail")

    def test_build_rejects_reserved_component_pages_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={
                    "site/pages/_index.md": text_block(
                        """
                        # Mammoth Cache

                        Landing page.
                        """
                    ),
                    "site/pages/development/overview.md": "# Bad path\n",
                },
                defaults=catalog_defaults(docsRoot="site/docs"),
            )

            with self.assertRaisesRegex(ValueError, "reserved staged path"):
                site_pipeline.build(repo_root)

    def test_build_rejects_component_pages_without_root_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"site/pages/getting-started.md": "# Getting started\n"},
            )

            with self.assertRaisesRegex(ValueError, "must contain _index.md"):
                site_pipeline.build(repo_root)

    def test_build_warns_when_docs_root_has_no_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={
                    "site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n",
                    "site/docs/getting-started.md": "# Getting started\n\nRead this first.\n",
                },
            )

            results = site_pipeline.build(repo_root)
            result = results[0]
            staged_doc = _staged_component_docs_root(repo_root) / "getting-started.md"

            self.assertTrue(staged_doc.is_file())
            self.assertIsNone(result.raw_docs_root_path)
            self.assertIn(
                "Docs root is missing _index.md; add a site-oriented docs landing page.",
                result.warnings,
            )

    def test_build_does_not_touch_preview_tree_when_preview_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n"},
            )
            preview_root = repo_root / "site" / ".preview"
            write_files(
                repo_root,
                {
                    "site/.preview/index.html": "old preview\n",
                    "site/.preview/assets/app.js": "console.log('keep');\n",
                },
            )

            site_pipeline.build(repo_root, include_preview=False)

            self.assertEqual("old preview\n", (preview_root / "index.html").read_text())
            self.assertEqual(
                "console.log('keep');\n",
                (preview_root / "assets" / "app.js").read_text(),
            )

    def test_build_stages_authored_site_pages_with_site_pipeline_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n"},
            )
            write_files(
                repo_root,
                {
                    "site/content/guide.md": "# Guide\n\nHello from the consumer site.\n",
                },
            )

            site_pipeline.build(repo_root, site_title="Friendly Site")

            staged_root_index = (repo_root / "site" / ".stage" / "content" / "_index.md").read_text()
            staged_guide = (repo_root / "site" / ".stage" / "content" / "guide.md").read_text()

            self.assertIn("title: Friendly Site", staged_root_index)
            self.assertIn("sitePipeline:", staged_root_index)
            self.assertIn("sitePipeline:", staged_guide)

    def test_build_records_assets_root_when_component_assets_are_staged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={
                    "site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n",
                    "site/assets/logo.svg": "<svg></svg>\n",
                },
            )

            results = site_pipeline.build(repo_root)
            result = results[0]
            staged_asset = _staged_component_assets_root(repo_root) / "logo.svg"

            self.assertEqual(1, result.asset_count)
            self.assertEqual(
                "/components/mammoth-cache/development/assets/",
                result.raw_assets_root_path,
            )
            self.assertTrue(staged_asset.is_file())

    def test_build_keeps_non_markdown_component_content_unmodified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={
                    "site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n",
                    "site/pages/guide.md": "# Guide\n\nMore detail.\n",
                    "site/pages/notes.txt": "plain notes\n",
                    "site/docs/_index.md": "# Docs\n\nRead me first.\n",
                    "site/docs/reference.adoc": "= Reference\n",
                    "site/docs/raw.txt": "raw text\n",
                },
            )

            results = site_pipeline.build(repo_root)
            result = results[0]
            staged_component_root = _staged_component_content_root(repo_root)
            staged_docs_root = _staged_component_docs_root(repo_root)
            staged_guide = (staged_component_root / "guide.md").read_text(encoding="utf-8")
            staged_notes = (staged_component_root / "notes.txt").read_text(encoding="utf-8")
            staged_reference = (staged_docs_root / "reference.adoc").read_text(encoding="utf-8")
            staged_raw = (staged_docs_root / "raw.txt").read_text(encoding="utf-8")

            self.assertIn("kind: component-page", staged_guide)
            self.assertEqual("plain notes\n", staged_notes)
            self.assertEqual("= Reference\n", staged_reference)
            self.assertEqual("raw text\n", staged_raw)
            self.assertEqual(
                ["Docs", "Reference"],
                [link.label for link in result.doc_links],
            )

    def test_build_allows_missing_authored_site_content_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n"},
            )

            site_pipeline.build(repo_root, authored_site_content_path="site/missing-content")

            self.assertFalse(
                (repo_root / "site" / ".stage" / "content" / "_index.md").exists()
            )

    def test_build_keeps_non_markdown_authored_site_files_unmodified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={"site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n"},
            )
            write_files(
                repo_root,
                {
                    "site/content/robots.txt": "User-agent: *\nDisallow:\n",
                },
            )

            site_pipeline.build(repo_root, site_title="Friendly Site")

            self.assertEqual(
                "User-agent: *\nDisallow:\n",
                (repo_root / "site" / ".stage" / "content" / "robots.txt").read_text(
                    encoding="utf-8"
                ),
            )

    def test_build_uses_explicit_component_tag_pattern_for_lifecycle_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = _seed_build_fixture(
                Path(temp_dir),
                component_files={
                    "site/pages/_index.md": "# Mammoth Cache\n\nLanding page.\n",
                    "site/component.yaml": (
                        "schemaVersion: 1\n"
                        "component:\n"
                        "  displayName: Mammoth Cache\n"
                        "versioning:\n"
                        "  tagPattern: ^release-[0-9]+$\n"
                        "lifecycle:\n"
                        "  latestStable: release-7\n"
                        "  releaseLines:\n"
                        "    - line: stable\n"
                        "      latest: release-7\n"
                        "      status: maintained\n"
                    ),
                },
            )

            result = site_pipeline.build(repo_root)[0]

            self.assertEqual("release-7", result.latest_stable_version)
            self.assertEqual("release-7", result.release_lines[0].latest)


class PreviewTest(unittest.TestCase):
    def test_preview_passes_missing_components_policy_to_build(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            stage_root = repo_root / "site" / ".stage"
            preview_root = repo_root / "site" / ".preview"

            class _StopPreview(RuntimeError):
                pass

            class _FakeServer:
                def __enter__(self) -> _FakeServer:
                    return self

                def __exit__(self, *args: object) -> None:
                    return None

                def serve_forever(self) -> None:
                    raise _StopPreview()

            with patch("apache_buildish_site_pipeline.builder.build") as build_mock, patch(
                "apache_buildish_site_pipeline.builder.resolve_workspace_paths",
                return_value=ResolvedWorkspacePaths(
                    repo_root=repo_root,
                    config_path=repo_root / "site" / "site-pipeline.yaml",
                    site_root=repo_root / "site",
                    authored_site_content_path=repo_root / "site" / "content",
                    stage_path=stage_root,
                    preview_path=preview_root,
                ),
            ), patch(
                "apache_buildish_site_pipeline.builder.socketserver.TCPServer",
                return_value=_FakeServer(),
            ):
                with self.assertRaises(_StopPreview):
                    site_pipeline.preview(repo_root, missing_components="fail")

            build_mock.assert_called_once_with(
                repo_root,
                config_path=None,
                catalog_path=None,
                authored_site_content_path=None,
                stage_path=None,
                preview_path=None,
                site_title=None,
                project_status=None,
                missing_components="fail",
            )


class CleanTest(unittest.TestCase):
    def test_clean_removes_configured_and_legacy_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {
                        "stagePath": "build/site-stage",
                        "previewPath": "build/site-preview",
                    },
                },
            )
            write_files(
                repo_root,
                {
                    "build/site-stage/manifest.yaml": "schemaVersion: 1\n",
                    "build/site-preview/index.html": "<html></html>\n",
                    ".site-stage/legacy.txt": "legacy stage\n",
                    ".site-preview/legacy.txt": "legacy preview\n",
                },
            )

            site_pipeline.clean(repo_root, config_path="site/site-pipeline.yaml")

            self.assertFalse((repo_root / "build" / "site-stage").exists())
            self.assertFalse((repo_root / "build" / "site-preview").exists())
            self.assertFalse((repo_root / ".site-stage").exists())
            self.assertFalse((repo_root / ".site-preview").exists())