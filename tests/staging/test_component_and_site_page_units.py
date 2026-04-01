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

"""Direct coverage for component and site-page staging workers."""

from __future__ import annotations

import frontmatter
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from buildish_site_pipeline.models.enums import RouteMode
from buildish_site_pipeline.staging.units.component import _copy_tree
from buildish_site_pipeline.staging.worker_entrypoint import execute_worker_spec
from buildish_site_pipeline.staging.worker_protocol import (
    WorkerSpecWire,
    WorkerResultWire,
    read_unit_manifest,
    worker_failure_result,
)


class ComponentAndSitePageUnitTests(unittest.TestCase):
    def test_worker_spec_coerces_localization_route_mode_to_enum(self) -> None:
        spec = WorkerSpecWire(
            unit_id="component:spark",
            unit_kind="component",
            owner_id="component:spark",
            workspace_root="/workspace",
            fragment_path="/workspace/.work/fragments/component_spark.json",
            localization={
                "default_locale": "en",
                "supported_locales": ("en", "fr"),
                "route_mode": "prefixAll",
            },
        )

        self.assertIs(spec.localization.route_mode, RouteMode.PREFIX_ALL)

    def test_component_worker_stages_pages_assets_and_contexts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            component_docs = root / "components/runtime/docs"
            component_assets = root / "components/runtime/assets"
            context_docs = root / "components/runtime/versions/4.0/docs"
            context_assets = root / "components/runtime/versions/4.0/assets"
            component_docs.mkdir(parents=True)
            component_assets.mkdir(parents=True)
            context_docs.mkdir(parents=True)
            context_assets.mkdir(parents=True)
            (component_docs / "index.md").write_text(
                "---\ntitle: Spark Home\nlinkTitle: Home\ntranslationKey: home\n---\nbody\n",
                encoding="utf-8",
            )
            (component_docs / "robots.txt").write_text("allow\n", encoding="utf-8")
            (component_assets / "logo.svg").write_text("<svg/>\n", encoding="utf-8")
            (context_docs / "guide.md").write_text(
                "# Version Guide\n\nInstall the runtime guide.\n",
                encoding="utf-8",
            )
            (context_assets / "download.zip").write_bytes(b"zip")

            component_stage_root = root / "stage/content/spark"
            component_assets_stage_root = root / "stage/static/spark/assets"
            context_stage_root = root / "stage/content/spark/4.0.0"
            context_static_root = root / "stage/static/spark/4.0.0"
            fragment_path = root / ".work/fragments/component_spark.json"

            result = execute_worker_spec(
                WorkerSpecWire(
                    unit_id="component:spark",
                    unit_kind="component",
                    owner_id="component:spark",
                    workspace_root=str(root),
                    unit_root=str(root / ".work/units/component_spark"),
                    fragment_path=str(fragment_path),
                    component_slug="spark",
                    component_pages_source=str(component_docs),
                    component_pages_stage_root=str(component_stage_root),
                    component_assets_source=str(component_assets),
                    component_assets_stage_root=str(component_assets_stage_root),
                    component_front_matter=self._component_front_matter(),
                    component_publication=self._publication_wire(
                        path="/spark/",
                        url="https://docs.example.org/spark/",
                    ),
                    localization={
                        "default_locale": "en",
                        "supported_locales": ("en", "fr"),
                        "route_mode": "prefixAll",
                    },
                    contexts=(
                        {
                            "context_id": "release:spark/runtime@4.0.0",
                            "artifact_key": "runtime",
                            "source_docs_root": str(context_docs),
                            "source_assets_root": str(context_assets),
                            "content_stage_root": str(context_stage_root),
                            "static_stage_root": str(context_static_root),
                            "publication": self._publication_wire(
                                path="/spark/4.0.0/",
                                url="https://docs.example.org/spark/4.0.0/",
                            ),
                            "version_context": {"label": "4.0.0"},
                            "page_kind": "version-page",
                            "section": "docs",
                            "record_kind": "released",
                            "version_ref": "refs/tags/v4.0.0",
                            "version": "4.0.0",
                        },
                    ),
                    stage_meta={
                        "content_roots": (
                            str(component_stage_root),
                            str(context_stage_root),
                        ),
                        "static_roots": (
                            str(component_assets_stage_root),
                            str(context_static_root),
                        ),
                    },
                )
            )

            manifest = read_unit_manifest(fragment_path)
            self.assertTrue(result.succeeded)
            self.assertEqual(result.output_stats.files_written, 5)
            self.assertEqual(result.output_stats.page_files_written, 2)
            self.assertEqual(result.output_stats.asset_files_written, 2)
            self.assertTrue((component_stage_root / "index.md").is_file())
            self.assertTrue((component_stage_root / "robots.txt").is_file())
            self.assertTrue((component_assets_stage_root / "logo.svg").is_file())
            self.assertTrue((context_stage_root / "guide.md").is_file())
            self.assertTrue((context_static_root / "download.zip").is_file())
            self.assertEqual(len(manifest.pages), 2)
            self.assertEqual(manifest.pages[0].locale, "en")
            self.assertTrue(manifest.pages[0].default_locale)
            self.assertEqual(manifest.pages[0].translation_key, "home")
            self.assertEqual(manifest.pages[0].title, "Spark Home")
            self.assertEqual(manifest.pages[0].link_title, "Home")
            self.assertEqual(manifest.pages[1].title, "Version Guide")
            self.assertEqual(
                manifest.pages[1].description, "Install the runtime guide."
            )
            self.assertEqual(manifest.pages[1].derived_title, "Version Guide")
            self.assertEqual(
                manifest.pages[1].derived_description,
                "Install the runtime guide.",
            )
            self.assertEqual(manifest.pages[1].version, "4.0.0")
            staged_post = frontmatter.load(context_stage_root / "guide.md")
            self.assertNotIn("title", staged_post.metadata)
            self.assertNotIn("description", staged_post.metadata)

    def test_component_worker_stages_component_owned_development_docs_without_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            development_docs = root / "components/site-pipeline/docs"
            development_docs.mkdir(parents=True)
            (development_docs / "index.md").write_text(
                "---\ntitle: Development Docs\n---\nbody\n",
                encoding="utf-8",
            )

            development_stage_root = root / "stage/content/components/site-pipeline/development"
            development_static_root = root / "stage/static/components/site-pipeline/development"
            fragment_path = root / ".work/fragments/component_site-pipeline.json"

            result = execute_worker_spec(
                WorkerSpecWire(
                    unit_id="component:site-pipeline",
                    unit_kind="component",
                    owner_id="component:site-pipeline",
                    workspace_root=str(root),
                    unit_root=str(root / ".work/units/component_site-pipeline"),
                    fragment_path=str(fragment_path),
                    component_slug="site-pipeline",
                    component_front_matter=self._component_front_matter(),
                    localization={
                        "default_locale": "en",
                        "supported_locales": ("en",),
                        "route_mode": "prefixAll",
                    },
                    contexts=(
                        {
                            "context_id": "development:site-pipeline:component",
                            "artifact_key": None,
                            "source_docs_root": str(development_docs),
                            "content_stage_root": str(development_stage_root),
                            "static_stage_root": str(development_static_root),
                            "publication": self._publication_wire(
                                path="/components/site-pipeline/development/",
                                url="https://docs.example.org/components/site-pipeline/development/",
                            ),
                            "version_context": {"label": "development", "kind": "development"},
                            "page_kind": "development-page",
                            "section": "development",
                            "record_kind": "development",
                        },
                    ),
                    stage_meta={
                        "content_roots": (str(development_stage_root),),
                        "static_roots": (str(development_static_root),),
                    },
                )
            )

            manifest = read_unit_manifest(fragment_path)
            self.assertTrue(result.succeeded)
            self.assertEqual(result.output_stats.page_files_written, 1)
            self.assertTrue((development_stage_root / "index.md").is_file())
            self.assertEqual(manifest.pages[0].artifact_key, None)
            self.assertEqual(manifest.pages[0].public_path, "/components/site-pipeline/development")

    def test_copy_tree_copies_nested_assets(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "source"
            target_root = root / "target"
            (source_root / "nested").mkdir(parents=True)
            (source_root / "nested/asset.txt").write_text("asset\n", encoding="utf-8")

            copied = _copy_tree(source_root, target_root)

            self.assertEqual(copied, 1)
            self.assertEqual(
                (target_root / "nested/asset.txt").read_text(encoding="utf-8"),
                "asset\n",
            )

    def test_site_pages_worker_stages_pages_and_non_page_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "site/content"
            target_root = root / "stage/content"
            source_root.mkdir(parents=True)
            (source_root / "index.md").write_text(
                "---\ntitle: Site Home\n---\nbody\n",
                encoding="utf-8",
            )
            (source_root / "guide.adoc").write_text(
                "---\ntranslationKey: guide\n---\n= Guide\n\nInstall the guide.\n",
                encoding="utf-8",
            )
            (source_root / "search.json").write_text("{}\n", encoding="utf-8")

            result = execute_worker_spec(
                WorkerSpecWire(
                    unit_id="site-pages",
                    unit_kind="site-pages",
                    owner_id="site-pages",
                    workspace_root=str(root),
                    fragment_path=str(root / ".work/fragments/site-pages.json"),
                    site_pages_source=str(source_root),
                    stage_meta={"content_roots": (str(target_root),)},
                )
            )
            self.assertTrue(result.succeeded)
            self.assertEqual(result.output_stats.files_written, 3)
            self.assertEqual(result.output_stats.page_files_written, 2)
            self.assertTrue((target_root / "index.md").is_file())
            self.assertTrue((target_root / "guide.adoc").is_file())
            self.assertEqual(
                (target_root / "search.json").read_text(encoding="utf-8"),
                "{}\n",
            )
            staged_post = frontmatter.load(target_root / "guide.adoc")
            self.assertEqual(staged_post["translationKey"], "guide")
            self.assertEqual(staged_post.content, "= Guide\n\nInstall the guide.")
            self.assertNotIn("title", staged_post.metadata)
            self.assertNotIn("description", staged_post.metadata)

    def test_require_success_raises_for_worker_failure_payloads(self) -> None:
        with self.assertRaisesRegex(Exception, "boom"):
            worker_failure_result(
                unit_id="component:spark",
                category="integrity",
                message="boom",
                stage_meta={"content_roots": (), "static_roots": ()},
            ).require_success()

        with self.assertRaisesRegex(Exception, "unknown worker failure"):
            WorkerResultWire(
                unit_id="component:spark",
                succeeded=False,
            ).require_success()

    @staticmethod
    def _publication_wire(*, path: str, url: str) -> dict[str, str]:
        return {
            "path": path,
            "url": url,
            "component_path": "/spark/",
            "component_url": "https://docs.example.org/spark/",
            "origin_key": "docs",
        }

    @staticmethod
    def _component_front_matter() -> dict[str, object]:
        return {
            "slug": "spark",
            "publication": {
                "origin": {
                    "key": "docs",
                    "base_url": "https://docs.example.org",
                    "hostname": "docs.example.org",
                },
                "paths": {
                    "component": "/spark/",
                    "development": "/spark/dev/",
                    "docs": "/spark/docs/",
                    "assets": "/spark/assets/",
                },
                "urls": {
                    "component": "https://docs.example.org/spark/",
                    "development": "https://docs.example.org/spark/dev/",
                    "docs": "https://docs.example.org/spark/docs/",
                    "assets": "https://docs.example.org/spark/assets/",
                },
            },
        }