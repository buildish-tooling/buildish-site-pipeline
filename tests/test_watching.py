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

"""Tests for watch-root calculation and watch-path filtering."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import redirect_stderr
from contextlib import redirect_stdout
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from apache_buildish_site_pipeline import collect_watch_roots
from apache_buildish_site_pipeline import is_relevant_watch_path
from apache_buildish_site_pipeline.config import ResolvedPipelineConfig
from apache_buildish_site_pipeline.filesystem import safe_relative_path as filesystem_safe_relative_path
from apache_buildish_site_pipeline.models import CatalogComponent
from apache_buildish_site_pipeline.models import ComponentCatalogDefaults
from apache_buildish_site_pipeline.watching import watch_and_build
from apache_buildish_site_pipeline.watching import _component_watch_roots
from apache_buildish_site_pipeline.watching import _format_watch_path
from apache_buildish_site_pipeline.watching import _local_pipeline_dependency_watch_path

from tests.test_support import catalog_defaults
from tests.test_support import catalog_payload
from tests.test_support import dump_yaml
from tests.test_support import text_block
from tests.test_support import write_files


def _seed_pipeline_stub(repo_root: Path, *, pyproject_text: str, content_path: str) -> None:
    write_files(
        repo_root,
        {
            "site/pipeline/main.py": "raise SystemExit(0)\n",
            "site/pipeline/pyproject.toml": pyproject_text,
            "site/pipeline/uv.lock": "version = 1\n",
            "site/pipeline/apache_buildish_site_pipeline/__init__.py": "",
            content_path: "# Root\n",
        },
    )


class _StopWatching(RuntimeError):
    """Signal used by tests to stop the watch loop deterministically."""


def _resolved_watch_config(
    repo_root: Path, *, missing_components: str = "warn"
) -> ResolvedPipelineConfig:
    return ResolvedPipelineConfig(
        repo_root=repo_root,
        config_path=repo_root / "site" / "site-pipeline.yaml",
        site_root=repo_root / "site",
        catalog_path=repo_root / "site" / "components.yaml",
        authored_site_content_path=repo_root / "site" / "content",
        stage_path=repo_root / "site" / ".stage",
        preview_path=repo_root / "site" / ".preview",
        site_title="Example Site",
        project_status="incubating",
        missing_components=missing_components,
    )


def _watchfiles_module(
    *event_batches: set[tuple[int, str]],
    assert_watch_filter: Callable[[Callable[..., bool]], None] | None = None,
) -> types.ModuleType:
    fake_watchfiles = types.ModuleType("watchfiles")

    def fake_watch(*args: object, **kwargs: object):
        watch_filter = kwargs["watch_filter"]
        if assert_watch_filter is not None:
            assert_watch_filter(watch_filter)
        yield from event_batches

    fake_watchfiles.watch = fake_watch
    return fake_watchfiles


class WatchRootsTest(unittest.TestCase):
    def test_local_pipeline_dependency_watch_path_rejects_invalid_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            project_root = repo_root / "site" / "pipeline"
            project_root.mkdir(parents=True)

            self.assertIsNone(_local_pipeline_dependency_watch_path(project_root, repo_root))

            for pyproject_text in (
                "[project]\nname='consumer'\n[tool.uv.sources]\napache-buildish-site-pipeline = 'wheel.whl'\n",
                "[project]\nname='consumer'\n[tool.uv.sources]\napache-buildish-site-pipeline = { path = '' }\n",
                (
                    "[project]\nname='consumer'\n[tool.uv.sources]\n"
                    "apache-buildish-site-pipeline = { path = '../../../../outside/pipeline' }\n"
                ),
            ):
                with self.subTest(pyproject_text=pyproject_text):
                    (project_root / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")
                    self.assertIsNone(
                        _local_pipeline_dependency_watch_path(project_root, repo_root)
                    )

    def test_component_watch_roots_allow_missing_optional_content_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            component_root = workspace / "mammoth-cache"
            dump_yaml(
                component_root / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth Cache"}},
            )

            roots = _component_watch_roots(
                repo_root,
                CatalogComponent(slug="mammoth-cache", local_dir="mammoth-cache"),
                ComponentCatalogDefaults(),
            )

        self.assertEqual({(component_root / "site" / "component.yaml").resolve()}, roots)

    def test_component_watch_roots_ignore_empty_optional_content_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            component_root = workspace / "mammoth-cache"
            dump_yaml(
                component_root / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth Cache"}},
            )

            roots = _component_watch_roots(
                repo_root,
                CatalogComponent(
                    slug="mammoth-cache",
                    local_dir="mammoth-cache",
                    pages_root="",
                    docs_root="",
                    assets_root="",
                ),
                ComponentCatalogDefaults(),
            )

        self.assertEqual({(component_root / "site" / "component.yaml").resolve()}, roots)

    def test_component_watch_roots_tolerate_missing_metadata_watch_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            component_root = workspace / "mammoth-cache"
            dump_yaml(
                component_root / "site" / "component.yaml",
                {
                    "schemaVersion": 1,
                    "component": {"displayName": "Mammoth Cache"},
                    "content": {"pagesRoot": "site/pages"},
                },
            )
            (component_root / "site" / "pages").mkdir(parents=True)

            # Intentionally patch the metadata watch path to exercise the
            # defensive branch where metadata resolution yields no watch root.
            def fake_safe_relative_path(base: Path, relative_path: str | None, label: str):
                if label == "metadataFile for mammoth-cache":
                    return None
                return filesystem_safe_relative_path(base, relative_path, label)

            with patch(
                "apache_buildish_site_pipeline.watching.safe_relative_path",
                side_effect=fake_safe_relative_path,
            ):
                roots = _component_watch_roots(
                    repo_root,
                    CatalogComponent(slug="mammoth-cache", local_dir="mammoth-cache"),
                    ComponentCatalogDefaults(),
                )

        self.assertEqual({(component_root / "site" / "pages").resolve()}, roots)

    def test_collect_watch_roots_uses_local_pipeline_snapshot_wheel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            wheel_path = (
                workspace
                / "buildish-site-pipeline"
                / "dist"
                / "snapshots"
                / "apache_buildish_site_pipeline-0.1.0.devfixture+gtest-py3-none-any.whl"
            )
            _seed_pipeline_stub(
                repo_root,
                pyproject_text=text_block(
                    """
                    [project]
                    name='consumer'

                    [tool.uv.sources]
                    apache-buildish-site-pipeline = { path = "../../../buildish-site-pipeline/dist/snapshots/apache_buildish_site_pipeline-0.1.0.devfixture+gtest-py3-none-any.whl" }
                    """
                ),
                content_path="site/content/_index.md",
            )
            wheel_path.parent.mkdir(parents=True, exist_ok=True)
            wheel_path.write_text("stub wheel\n", encoding="utf-8")
            dump_yaml(repo_root / "site" / "components.yaml", catalog_payload())

            watch_roots = set(collect_watch_roots(repo_root))

            self.assertIn(wheel_path.resolve(), watch_roots)
            self.assertNotIn(
                (repo_root / "site" / "pipeline" / "apache_buildish_site_pipeline").resolve(),
                watch_roots,
            )

    def test_collect_watch_roots_includes_existing_vendor_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            write_files(
                repo_root,
                {
                    "site/node_modules/jquery/dist/jquery.min.js": "jquery\n",
                },
            )
            dump_yaml(repo_root / "site" / "components.yaml", catalog_payload())

            watch_roots = set(collect_watch_roots(repo_root))

        self.assertIn(
            (repo_root / "site" / "node_modules" / "jquery" / "dist" / "jquery.min.js").resolve(),
            watch_roots,
        )

    def test_collect_watch_roots_uses_components_local_yaml_checkout_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            _seed_pipeline_stub(
                repo_root,
                pyproject_text="[project]\nname='stub'\n",
                content_path="site/content/_index.md",
            )
            dump_yaml(
                repo_root / "site" / "components.yaml",
                catalog_payload(
                    {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
                    defaults=catalog_defaults(),
                ),
            )
            dump_yaml(
                repo_root / "site" / "components.local.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {
                        "components": {"mammoth-cache": {"checkoutDir": "../src/mammoth-cache"}}
                    },
                },
            )

            mammoth = workspace / "src" / "mammoth-cache"
            write_files(mammoth, {"site/pages/_index.md": "# Mammoth\n\nLanding page.\n"})
            (mammoth / "site" / "docs").mkdir(parents=True)
            (mammoth / "site" / "assets").mkdir(parents=True)
            dump_yaml(
                mammoth / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth"}},
            )

            watch_roots = set(collect_watch_roots(repo_root))

            self.assertIn((repo_root / "site" / "components.local.yaml").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "component.yaml").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "pages").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "docs").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "assets").resolve(), watch_roots)

    def test_collect_watch_roots_ignores_missing_component_checkout_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            _seed_pipeline_stub(
                repo_root,
                pyproject_text="[project]\nname='stub'\n",
                content_path="site/content/_index.md",
            )
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {"schemaVersion": 1, "site": {"projectStatus": "incubating"}},
            )
            (repo_root / "site" / "pipeline" / ".venv" / "bin").mkdir(parents=True)
            (repo_root / "site" / "pipeline" / ".idea").mkdir(parents=True)
            dump_yaml(
                repo_root / "site" / "components.yaml",
                catalog_payload(
                    {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
                    {"slug": "missing-component", "localDir": "missing-component"},
                    defaults=catalog_defaults(),
                ),
            )

            mammoth = workspace / "mammoth-cache"
            write_files(mammoth, {"site/pages/_index.md": "# Mammoth\n\nLanding page.\n"})
            (mammoth / "site" / "docs").mkdir(parents=True)
            (mammoth / "site" / "assets").mkdir(parents=True)
            dump_yaml(
                mammoth / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth"}},
            )

            watch_roots = set(collect_watch_roots(repo_root))

            self.assertIn((repo_root / "site" / "components.yaml").resolve(), watch_roots)
            self.assertIn((repo_root / "site" / "site-pipeline.yaml").resolve(), watch_roots)
            self.assertIn((repo_root / "site" / "content").resolve(), watch_roots)
            self.assertIn((repo_root / "site" / "pipeline" / "main.py").resolve(), watch_roots)
            self.assertIn((repo_root / "site" / "pipeline" / "pyproject.toml").resolve(), watch_roots)
            self.assertIn((repo_root / "site" / "pipeline" / "uv.lock").resolve(), watch_roots)
            self.assertIn(
                (repo_root / "site" / "pipeline" / "apache_buildish_site_pipeline").resolve(),
                watch_roots,
            )
            self.assertIn((mammoth / "site" / "component.yaml").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "pages").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "docs").resolve(), watch_roots)
            self.assertIn((mammoth / "site" / "assets").resolve(), watch_roots)
            self.assertNotIn(workspace.resolve(), watch_roots)
            self.assertNotIn((workspace / "missing-component").resolve(), watch_roots)
            self.assertNotIn((repo_root / "site" / "pipeline").resolve(), watch_roots)
            self.assertNotIn((repo_root / "site" / "pipeline" / ".venv").resolve(), watch_roots)

    def test_collect_watch_roots_uses_configured_catalog_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            _seed_pipeline_stub(
                repo_root,
                pyproject_text="[project]\nname='stub'\n",
                content_path="site/content/_index.md",
            )
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {"schemaVersion": 1, "workspace": {"catalogPath": "site/catalogs/components.yaml"}},
            )
            dump_yaml(
                repo_root / "site" / "catalogs" / "components.yaml",
                catalog_payload(
                    {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
                    defaults=catalog_defaults(),
                ),
            )

            mammoth = workspace / "mammoth-cache"
            write_files(mammoth, {"site/pages/_index.md": "# Mammoth\n\nLanding page.\n"})
            (mammoth / "site" / "docs").mkdir(parents=True)
            (mammoth / "site" / "assets").mkdir(parents=True)
            dump_yaml(
                mammoth / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth"}},
            )

            watch_roots = set(collect_watch_roots(repo_root))

            self.assertIn((repo_root / "site" / "catalogs" / "components.yaml").resolve(), watch_roots)
            self.assertNotIn((repo_root / "site" / "components.yaml").resolve(), watch_roots)

    def test_collect_watch_roots_uses_configured_authored_site_content_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            _seed_pipeline_stub(
                repo_root,
                pyproject_text="[project]\nname='stub'\n",
                content_path="docs-src/_index.md",
            )
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {"schemaVersion": 1, "workspace": {"authoredSiteContentPath": "docs-src"}},
            )
            dump_yaml(
                repo_root / "site" / "components.yaml",
                catalog_payload(
                    {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
                    defaults=catalog_defaults(),
                ),
            )

            mammoth = workspace / "mammoth-cache"
            write_files(mammoth, {"site/pages/_index.md": "# Mammoth\n\nLanding page.\n"})
            (mammoth / "site" / "docs").mkdir(parents=True)
            dump_yaml(
                mammoth / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth"}},
            )

            watch_roots = set(collect_watch_roots(repo_root))

            self.assertIn((repo_root / "docs-src").resolve(), watch_roots)
            self.assertNotIn((repo_root / "site" / "content").resolve(), watch_roots)


class WatchPathFilterTest(unittest.TestCase):
    def test_is_relevant_watch_path_allows_explicit_vendor_asset_paths(self) -> None:
        self.assertTrue(
            is_relevant_watch_path(Path("site/node_modules/jquery/dist/jquery.min.js"))
        )
        self.assertFalse(is_relevant_watch_path(Path("site/.stage/content/_index.md")))

    def test_is_relevant_watch_path_rejects_editor_temporary_names(self) -> None:
        self.assertFalse(is_relevant_watch_path(Path("docs/.#guide.md")))
        self.assertFalse(is_relevant_watch_path(Path("docs/4913")))
        self.assertFalse(is_relevant_watch_path(Path("docs/guide.md.tmp")))

    def test_format_watch_path_falls_back_to_absolute_path_outside_workspace(self) -> None:
        self.assertEqual(
            "/outside/guide.md",
            _format_watch_path(Path("/outside/guide.md"), Path("/workspace/consumer")),
        )


class WatchBuildLoopTest(unittest.TestCase):
    def test_watch_and_build_ignores_irrelevant_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            watch_roots = [repo_root / "site" / "components.yaml"]

            def assert_watch_filter(watch_filter: Callable[..., bool]) -> None:
                self.assertTrue(watch_filter(None, str(repo_root / "site" / "components.yaml")))
                self.assertFalse(
                    watch_filter(None, str(repo_root / "site" / "components.yaml.tmp"))
                )

            with patch(
                "apache_buildish_site_pipeline.watching.resolve_pipeline_config",
                return_value=_resolved_watch_config(repo_root),
            ), patch(
                "apache_buildish_site_pipeline.watching.collect_watch_roots",
                side_effect=[watch_roots, _StopWatching()],
            ), patch(
                "apache_buildish_site_pipeline.watching.build",
                return_value=[object()],
            ) as build_mock, patch.dict(
                sys.modules,
                {
                    "watchfiles": _watchfiles_module(
                        {(1, str(repo_root / "site" / "components.yaml.tmp"))},
                        assert_watch_filter=assert_watch_filter,
                    )
                },
            ):
                with self.assertRaises(_StopWatching):
                    watch_and_build(repo_root)

            self.assertEqual(1, build_mock.call_count)

    def test_watch_and_build_passes_missing_components_policy_to_rebuilds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            watch_roots = [repo_root / "site" / "components.yaml"]

            with patch(
                "apache_buildish_site_pipeline.watching.resolve_pipeline_config",
                return_value=_resolved_watch_config(repo_root, missing_components="fail"),
            ), patch(
                "apache_buildish_site_pipeline.watching.collect_watch_roots",
                side_effect=[watch_roots, watch_roots, _StopWatching()],
            ), patch(
                "apache_buildish_site_pipeline.watching.build",
                return_value=[object()],
            ) as build_mock, patch.dict(
                sys.modules,
                {
                    "watchfiles": _watchfiles_module(
                        {(1, str(repo_root / "site" / "components.yaml"))}
                    )
                },
            ):
                with self.assertRaises(_StopWatching):
                    watch_and_build(repo_root, missing_components="fail")

            self.assertEqual(2, build_mock.call_count)
            for call in build_mock.call_args_list:
                self.assertEqual(repo_root, call.args[0])
                self.assertEqual("fail", call.kwargs["missing_components"])
                self.assertFalse(call.kwargs["include_preview"])
                self.assertFalse(call.kwargs["warn_on_local_overrides"])

    def test_watch_and_build_warns_once_when_local_overrides_are_active(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            site_root = repo_root / "site"
            watch_roots = [site_root / "components.yaml"]
            stderr = io.StringIO()
            site_root.mkdir(parents=True)
            site_root.joinpath("components.local.yaml").write_text(
                "schemaVersion: 1\n"
                "workspace:\n"
                "  components:\n"
                "    mammoth-cache:\n"
                "      checkoutDir: ../mammoth-cache\n"
            )

            with patch(
                "apache_buildish_site_pipeline.watching.resolve_pipeline_config",
                return_value=_resolved_watch_config(repo_root),
            ), patch(
                "apache_buildish_site_pipeline.watching.collect_watch_roots",
                side_effect=[watch_roots, watch_roots, _StopWatching()],
            ), patch(
                "apache_buildish_site_pipeline.watching.build",
                return_value=[object()],
            ) as build_mock, patch.dict(
                sys.modules,
                {
                    "watchfiles": _watchfiles_module(
                        {(1, str(repo_root / "site" / "components.yaml"))}
                    )
                },
            ), redirect_stderr(stderr):
                with self.assertRaises(_StopWatching):
                    watch_and_build(repo_root)

            self.assertEqual(2, build_mock.call_count)
            self.assertEqual(1, stderr.getvalue().count("site/components.local.yaml"))

    def test_watch_and_build_reports_rebuild_and_watch_root_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            watch_roots = [repo_root / "site" / "components.yaml"]
            stderr = io.StringIO()

            with patch(
                "apache_buildish_site_pipeline.watching.resolve_pipeline_config",
                return_value=_resolved_watch_config(repo_root),
            ), patch(
                "apache_buildish_site_pipeline.watching.collect_watch_roots",
                side_effect=[watch_roots, RuntimeError("roots failed"), _StopWatching()],
            ), patch(
                "apache_buildish_site_pipeline.watching.build",
                side_effect=[[object()], RuntimeError("boom")],
            ), patch.dict(
                sys.modules,
                {
                    "watchfiles": _watchfiles_module(
                        {(1, str(repo_root / "site" / "components.yaml"))}
                    )
                },
            ), redirect_stderr(stderr):
                with self.assertRaises(_StopWatching):
                    watch_and_build(repo_root)

            self.assertIn("Rebuild failed: boom", stderr.getvalue())
            self.assertIn("Re-evaluating watch roots failed: roots failed", stderr.getvalue())

    def test_watch_and_build_restarts_when_watch_roots_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            watch_roots = [repo_root / "site" / "components.yaml"]
            updated_watch_roots = [repo_root / "site" / "site-pipeline.yaml"]
            stdout = io.StringIO()

            with patch(
                "apache_buildish_site_pipeline.watching.resolve_pipeline_config",
                return_value=_resolved_watch_config(repo_root),
            ), patch(
                "apache_buildish_site_pipeline.watching.collect_watch_roots",
                side_effect=[watch_roots, updated_watch_roots, _StopWatching()],
            ), patch(
                "apache_buildish_site_pipeline.watching.build",
                return_value=[object()],
            ), patch.dict(
                sys.modules,
                {
                    "watchfiles": _watchfiles_module(
                        {(1, str(repo_root / "site" / "components.yaml"))}
                    )
                },
            ), redirect_stdout(stdout):
                with self.assertRaises(_StopWatching):
                    watch_and_build(repo_root)

            self.assertIn("Watch roots changed; restarting watcher.", stdout.getvalue())