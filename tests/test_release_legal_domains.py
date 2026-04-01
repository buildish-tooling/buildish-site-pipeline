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

"""Focused contracts for extracted release-legal implementation domains."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from buildish_site_pipeline.legal import release_legal
from buildish_site_pipeline.legal.container_inventory import (
    bundled_container_image_refs,
    collect_container_base_image_entries,
    collect_curated_legal_files,
)
from buildish_site_pipeline.legal.license_policy import (
    spdx_expression_is_category_x,
)


class ReleaseLegalFacadeTests(unittest.TestCase):
    """Keep the pre-decomposition public helper surface available."""

    def test_facade_exports_prior_public_helpers(self) -> None:
        expected = {
            "CapturedLegalFile",
            "ContainerBuildStage",
            "CuratedContainerImageBundle",
            "DistributionInventoryEntry",
            "LockedPackage",
            "ProjectUrl",
            "ReleaseLegalReport",
            "build_curated_container_image_entry",
            "build_distribution_inventory_entry",
            "build_inventory_markdown",
            "build_preliminary_license_text",
            "build_preliminary_notice_text",
            "build_release_legal_report",
            "bundled_container_image_refs",
            "collect_container_base_image_entries",
            "collect_curated_legal_files",
            "collect_distribution_legal_files",
            "collect_included_stage_indexes",
            "curated_container_image_bundles_by_ref",
            "export_locked_runtime_packages",
            "generate_release_legal_artifacts",
            "installed_distributions_by_name",
            "locked_runtime_packages_from_pylock_text",
            "main",
            "normalize_distribution_name",
            "parse_container_build_stages",
            "write_release_legal_output",
        }

        self.assertEqual(set(release_legal.__all__), expected)
        self.assertTrue(all(hasattr(release_legal, name) for name in expected))


class ReleaseLegalPolicyTests(unittest.TestCase):
    """Verify Category X expression semantics independently of inventory I/O."""

    def test_spdx_policy_handles_and_or_parentheses_and_classpath_exception(self) -> None:
        cases = {
            "MIT": False,
            "GPL-3.0-only": True,
            "MIT OR GPL-3.0-only": False,
            "MIT AND GPL-3.0-only": True,
            "(GPL-3.0-only OR MIT) AND Apache-2.0": False,
            "GPL-2.0-only WITH Classpath-exception-2.0": False,
            "GPL-2.0-only WITH LLVM-exception": True,
        }

        for expression, expected in cases.items():
            with self.subTest(expression=expression):
                self.assertEqual(spdx_expression_is_category_x(expression), expected)

    def test_spdx_policy_rejects_incomplete_or_unbalanced_expressions(self) -> None:
        for expression in ("MIT AND", "(MIT OR GPL-3.0-only"):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                spdx_expression_is_category_x(expression)


class ReleaseLegalContainerInventoryTests(unittest.TestCase):
    """Verify container-stage selection and curated legal-file boundaries."""

    def test_bundled_refs_include_only_final_stage_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            containerfile = Path(temp_dir) / "Containerfile"
            containerfile.write_text(
                "\n".join(
                    (
                        "FROM example.invalid/unused:1 AS unused",
                        "FROM example.invalid/uv:2 AS uvbin",
                        "FROM example.invalid/python:3 AS runtime",
                        "COPY --from=uvbin /uv /bin/uv",
                        "COPY --from=example.invalid/external:4 /tool /tool",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            refs = bundled_container_image_refs(containerfile)

        self.assertEqual(
            refs,
            (
                "example.invalid/uv:2",
                "example.invalid/python:3",
                "example.invalid/external:4",
            ),
        )

    def test_container_inventory_requires_manifest_when_containerfile_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            containerfile = root / "tools" / "site-pipeline-image" / "Containerfile"
            containerfile.parent.mkdir(parents=True)
            containerfile.write_text("FROM example.invalid/python:3\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "no curated base-image"):
                collect_container_base_image_entries(root)

    def test_curated_legal_files_report_decode_replacement_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            license_path = root / "LICENSE.bin"
            license_path.write_bytes(b"license\xff")

            captured = collect_curated_legal_files(
                component_key="runtime",
                component_kind="container-base-image",
                license_paths=(license_path,),
                notice_paths=(),
            )

            self.assertEqual(len(captured), 1)
            self.assertEqual(
                captured[0].output_relative_path,
                "licenses/container-base-images/runtime/LICENSE.bin",
            )
            self.assertIsNotNone(captured[0].decode_warning)
            self.assertTrue(captured[0].text.endswith("\n"))

            with self.assertRaisesRegex(RuntimeError, "Missing curated notice file"):
                collect_curated_legal_files(
                    component_key="runtime",
                    component_kind="container-base-image",
                    license_paths=(),
                    notice_paths=(root / "missing-NOTICE",),
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
