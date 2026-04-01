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

"""Tests for rendering helpers and lightweight preview pages."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.models import ComponentBuildResult
from apache_buildish_site_pipeline.models import ComponentLifecycleReleaseLine
from apache_buildish_site_pipeline.models import ComponentLifecycleSettings
from apache_buildish_site_pipeline.models import StagedDocLink
from apache_buildish_site_pipeline.models import StagedReleaseLine
from apache_buildish_site_pipeline.rendering import build_component_preview
from apache_buildish_site_pipeline.rendering import build_preview_index
from apache_buildish_site_pipeline.rendering import normalize_lifecycle
from apache_buildish_site_pipeline.rendering import public_content_page_path
from apache_buildish_site_pipeline.rendering import public_directory_path


def _component_result(**overrides: object) -> ComponentBuildResult:
    payload: dict[str, object] = {
        "slug": "mammoth-cache",
        "display_name": "Mammoth Cache",
        "navigation_weight": 10,
        "available": True,
        "repository": "https://example.invalid/mammoth-cache",
        "local_dir": "mammoth-cache",
        "repo_path": Path("/workspace/mammoth-cache"),
        "summary": "Secure wrapper provisioning.",
        "raw_development_index_path": "/components/mammoth-cache/development/",
        "raw_component_index_path": "/components/mammoth-cache/",
        "raw_docs_root_path": "/components/mammoth-cache/development/docs/",
        "raw_assets_root_path": "/components/mammoth-cache/development/assets/",
        "development_label": "Preview",
        "default_branch": "main",
        "navigation_section": "components",
        "asset_count": 2,
        "latest_stable_version": "v1.2.3",
        "latest_stable_path": "/components/mammoth-cache/releases/v1.2.3/",
        "release_lines": (
            StagedReleaseLine(
                line="v1",
                latest="v1.2.3",
                status="maintained",
                aliases=("stable",),
                path="/components/mammoth-cache/releases/v1.2.3/",
            ),
        ),
        "alias_mappings": (),
        "doc_links": (
            StagedDocLink(
                label="Getting started",
                href="/components/mammoth-cache/development/docs/getting-started/",
            ),
        ),
        "warnings": ["Missing release notes"],
    }
    payload.update(overrides)
    return ComponentBuildResult(**payload)


class RenderingPathTest(unittest.TestCase):
    def test_public_paths_normalize_directory_and_markdown_routes(self) -> None:
        self.assertEqual("/", public_directory_path(Path(".")))
        self.assertEqual("/components/mammoth-cache/", public_directory_path(Path("components/mammoth-cache")))
        self.assertEqual(
            "/components/mammoth-cache/",
            public_content_page_path([], Path("components/mammoth-cache/_index.md")),
        )
        self.assertEqual(
            "/components/mammoth-cache/docs/getting-started/",
            public_content_page_path(
                [],
                Path("components/mammoth-cache/docs/getting-started.md"),
            ),
        )


class LifecycleRenderingTest(unittest.TestCase):
    def test_normalize_lifecycle_returns_release_lines_aliases_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stage_content_root = Path(temp_dir) / "stage" / "content"
            component_root = stage_content_root / "components" / "mammoth-cache"
            release_index = component_root / "releases" / "v1.2.3" / "_index.md"
            release_index.parent.mkdir(parents=True, exist_ok=True)
            release_index.write_text("# Release\n", encoding="utf-8")

            latest_stable, latest_path, release_lines, alias_mappings = normalize_lifecycle(
                ComponentLifecycleSettings(
                    latest_stable="v1.2.3",
                    release_lines=(
                        ComponentLifecycleReleaseLine(
                            line="v1",
                            latest="v1.2.3",
                            status="maintained",
                            aliases=("stable", "v1"),
                        ),
                    ),
                ),
                re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$"),
                "mammoth-cache",
                component_root,
                stage_content_root,
            )

        self.assertEqual("v1.2.3", latest_stable)
        self.assertEqual("/components/mammoth-cache/releases/v1.2.3/", latest_path)
        self.assertEqual(("stable", "v1"), release_lines[0].aliases)
        self.assertEqual("/components/mammoth-cache/releases/v1.2.3/", release_lines[0].path)
        self.assertEqual(["stable", "v1"], [entry.alias for entry in alias_mappings])


class PreviewRenderingTest(unittest.TestCase):
    def test_build_preview_index_lists_component_statuses(self) -> None:
        preview = build_preview_index(
            [
                _component_result(),
                _component_result(
                    slug="missing-cache",
                    display_name="Missing Cache",
                    available=False,
                ),
            ],
            site_title="Example Buildish",
            preview_root_path="/preview/",
            staged_root_markdown_path="/stage/content/_index.md",
        )

        self.assertIn("Example Buildish", preview)
        self.assertIn("href='/preview/components/mammoth-cache/'", preview)
        self.assertIn("missing from local workspace", preview)

    def test_build_component_preview_renders_doc_links_release_lines_and_warnings(self) -> None:
        preview = build_component_preview(_component_result(), "/preview/")

        self.assertIn("&larr; Back to preview index", preview)
        self.assertIn("Getting started", preview)
        self.assertIn("Missing release notes", preview)
        self.assertIn("Open staged component landing page", preview)
        self.assertIn("/components/mammoth-cache/releases/v1.2.3/", preview)