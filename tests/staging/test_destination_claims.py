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

"""Concrete file, rendered destination, and retained inventory ownership."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.staging.destination_claims import (
    DestinationClaim,
    collect_destination_claims,
    reconcile_candidate_files,
    validate_destination_claims,
)
from tests.staging.test_artifact_routes import planning
from tests.support.workspace import _workspace


class DestinationClaimTests(unittest.TestCase):
    def test_public_file_directory_and_page_index_conflicts_across_stage_trees(self):
        for static_path in (
            "/guide",
            "/guide/index.html",
            "/GUIDE/index.html",
            "/guide/index.html/child.svg",
        ):
            with self.subTest(static_path=static_path):
                claims = (
                    DestinationClaim(
                        "docs",
                        "docs/guide.md",
                        "/guide",
                        stage_path=Path("content/guide.md"),
                        page=True,
                    ),
                    DestinationClaim(
                        "assets",
                        "assets/file",
                        static_path,
                        stage_path=Path("static") / static_path.strip("/"),
                    ),
                )
                with self.assertRaisesRegex(
                    StageIntegrityError, "Destination conflict"
                ):
                    validate_destination_claims(claims)

    def test_equal_bytes_and_same_producer_never_hide_duplicate_claims(self):
        claim = DestinationClaim(
            "docs",
            "docs/guide.md",
            "/guide",
            stage_path=Path("content/guide.md"),
            page=True,
        )
        with self.assertRaisesRegex(StageIntegrityError, "Destination conflict"):
            validate_destination_claims((claim, claim))

    def test_page_container_accepts_child_page_and_disjoint_assets(self):
        validate_destination_claims(
            (
                DestinationClaim(
                    "guide",
                    "guide.md",
                    "/guide",
                    stage_path=Path("content/guide.md"),
                    page=True,
                ),
                DestinationClaim(
                    "child",
                    "guide/child.md",
                    "/guide/child",
                    stage_path=Path("content/guide/child.md"),
                    page=True,
                ),
                DestinationClaim(
                    "asset",
                    "guide/image.svg",
                    "/guide/image.svg",
                    stage_path=Path("static/guide/image.svg"),
                ),
            )
        )

    def test_mount_reserves_subtree_with_selection_independent_and_origin_aware_claims(
        self,
    ):
        mount = DestinationClaim(
            "mount", "generated/api", "/api/", "docs", kind="mount"
        )
        for other in (
            DestinationClaim(
                "child-mount",
                "generated/other",
                "/api/reference/",
                "docs",
                kind="mount",
            ),
            DestinationClaim(
                "context", "docs", "/api/development/", "docs", kind="context"
            ),
            DestinationClaim("redirect", "catalog", "/api/", "docs", kind="redirect"),
        ):
            with (
                self.subTest(other=other.kind),
                self.assertRaisesRegex(StageIntegrityError, "Destination conflict"),
            ):
                validate_destination_claims((mount, other))
        validate_destination_claims(
            (mount, DestinationClaim("container", "docs", "/", "docs", kind="context"))
        )
        validate_destination_claims(
            (
                mount,
                DestinationClaim(
                    "other-origin", "docs", "/api/", "archive", kind="context"
                ),
            )
        )

    def test_incomplete_claim_inventory_is_an_error(self):
        with _workspace(with_content_file=True) as root:
            result = planning(root)
            with patch(
                "buildish_site_pipeline.staging.destination_claims._MAX_DESTINATION_CLAIMS",
                1,
            ):
                with self.assertRaisesRegex(
                    StageIntegrityError, "validation is incomplete"
                ):
                    collect_destination_claims(
                        result.site, result.selected_versions.contexts
                    )

    def test_actual_retained_static_file_cannot_hide_behind_fresh_page_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            page = root / "content/guide.md"
            page.parent.mkdir(parents=True)
            page.write_text("fresh guide")
            unexpected = root / "static/guide/index.html"
            unexpected.parent.mkdir(parents=True)
            unexpected.write_text("unmanifested retained file")
            claims = (
                DestinationClaim(
                    "fresh",
                    "guide.md",
                    "/guide",
                    stage_path=Path("content/guide.md"),
                    page=True,
                ),
            )
            with self.assertRaisesRegex(
                StageIntegrityError, "Unexpected candidate file"
            ):
                reconcile_candidate_files(root, claims, ())
