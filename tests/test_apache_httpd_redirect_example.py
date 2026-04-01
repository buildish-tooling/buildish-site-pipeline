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

"""Exercise the copyable Apache httpd redirect adapter example."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from examples.apache_httpd.generate_redirects import (
    AdapterError,
    render_apache_redirects,
    write_apache_redirects,
)


class ApacheHttpdRedirectExampleTests(unittest.TestCase):
    """Protect exact, deterministic, and fail-closed config generation."""

    def test_renders_origin_scoped_exact_rules_with_preserved_statuses(self) -> None:
        items = [
            _redirect("https://other.example.org/ignored/", status=302),
            _redirect("http://docs.example.org/insecure/", status=301),
            _redirect("https://docs.example.org:8443/admin/", status=302),
            _redirect("https://docs.example.org/temporary/", status=307),
            _redirect("https://docs.example.org/old+(draft)/", status=308),
            _redirect("https://docs.example.org/moved/", status=301),
            _redirect("https://docs.example.org/found/", status=302),
        ]
        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            _create_stage(stage_root, items, redirects_path="metadata/rules.json")

            rendered = render_apache_redirects(
                stage_root=stage_root,
                source_origin="https://DOCS.EXAMPLE.ORG./",
            )

        self.assertEqual(
            """# Generated from Site Pipeline staged redirect metadata.
# Target source origin: https://docs.example.org
# Include in server or VirtualHost context; do not use in .htaccess.
RewriteEngine On

RewriteCond "%{HTTPS}" "^on$" [NC]
RewriteCond "%{HTTP_HOST}" "^docs\\.example\\.org(?::443)?$" [NC]
RewriteRule "^/found/$" "https://new.example.org/found/?source=old#start" [R=302,L,NE,QSD]

RewriteCond "%{HTTPS}" "^on$" [NC]
RewriteCond "%{HTTP_HOST}" "^docs\\.example\\.org(?::443)?$" [NC]
RewriteRule "^/moved/$" "https://new.example.org/moved/?source=old#start" [R=301,L,NE,QSD]

RewriteCond "%{HTTPS}" "^on$" [NC]
RewriteCond "%{HTTP_HOST}" "^docs\\.example\\.org(?::443)?$" [NC]
RewriteRule "^/old\\+\\(draft\\)/$" "https://new.example.org/old+(draft)/?source=old#start" [R=308,L,NE,QSD]

RewriteCond "%{HTTPS}" "^on$" [NC]
RewriteCond "%{HTTP_HOST}" "^docs\\.example\\.org(?::443)?$" [NC]
RewriteRule "^/temporary/$" "https://new.example.org/temporary/?source=old#start" [R=307,L,NE,QSD]
""",
            rendered,
        )

    def test_output_is_deterministic_regardless_of_aggregate_order(self) -> None:
        items = [
            _redirect("https://docs.example.org/z/", status=308),
            _redirect("https://docs.example.org/a/", status=301),
        ]
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            first_stage = root / "first"
            second_stage = root / "second"
            _create_stage(first_stage, items)
            _create_stage(second_stage, list(reversed(items)))

            first = render_apache_redirects(
                stage_root=first_stage,
                source_origin="https://docs.example.org",
            )
            second = render_apache_redirects(
                stage_root=second_stage,
                source_origin="https://docs.example.org",
            )

        self.assertEqual(first, second)

    def test_selects_scheme_and_port_without_collapsing_distinct_origins(self) -> None:
        items = [
            _redirect(
                "http://docs.example.org/same/",
                to_url="https://new.example.org/from-http/",
            ),
            _redirect(
                "https://docs.example.org/same/",
                to_url="https://new.example.org/from-https/",
            ),
            _redirect(
                "https://docs.example.org:8443/same/",
                to_url="https://new.example.org/from-8443/",
            ),
        ]
        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            _create_stage(stage_root, items)

            http_rendered = render_apache_redirects(
                stage_root=stage_root,
                source_origin="http://docs.example.org:80",
            )
            custom_port_rendered = render_apache_redirects(
                stage_root=stage_root,
                source_origin="https://docs.example.org:8443",
            )

        self.assertIn('RewriteCond "%{HTTPS}" "!^on$" [NC]', http_rendered)
        self.assertIn(
            'RewriteCond "%{HTTP_HOST}" "^docs\\.example\\.org(?::80)?$" [NC]',
            http_rendered,
        )
        self.assertIn("from-http", http_rendered)
        self.assertNotIn("from-https", http_rendered)
        self.assertNotIn("from-8443", http_rendered)
        self.assertIn('RewriteCond "%{HTTPS}" "^on$" [NC]', custom_port_rendered)
        self.assertIn(
            'RewriteCond "%{HTTP_HOST}" "^docs\\.example\\.org:8443$" [NC]',
            custom_port_rendered,
        )
        self.assertIn("from-8443", custom_port_rendered)
        self.assertNotIn("from-https", custom_port_rendered)

    def test_script_writes_the_requested_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "stage"
            output_path = root / "redirects.conf"
            _create_stage(stage_root, [_redirect("https://docs.example.org/old/")])

            result = subprocess.run(  # noqa: S603 -- fixed interpreter and script
                (
                    sys.executable,
                    "examples/apache_httpd/generate_redirects.py",
                    str(stage_root),
                    "https://docs.example.org",
                    str(output_path),
                ),
                cwd=Path(__file__).parents[1],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual("", result.stdout)
            self.assertEqual("", result.stderr)
            self.assertEqual(0, result.returncode)
            self.assertIn('RewriteRule "^/old/$"', output_path.read_text("utf-8"))

    def test_rejects_malformed_manifest_and_aggregate_documents(self) -> None:
        cases = (
            (
                {"stageLayoutVersion": 1, "aggregateFormat": "json"},
                {},
                "manifest schema version 1",
            ),
            (
                {
                    "schemaVersion": 2,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                },
                {},
                "manifest schema version 1",
            ),
            (
                {
                    "schemaVersion": True,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                },
                {},
                "manifest schema version 1",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 2,
                    "aggregateFormat": "json",
                },
                {},
                "layout version 1",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": True,
                    "aggregateFormat": "json",
                },
                {},
                "layout version 1",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "yaml",
                },
                {},
                "only JSON",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                },
                {},
                "declare dataFiles",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                    "dataFiles": {"redirects": "../outside.json"},
                },
                {},
                "stage-relative",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                    "dataFiles": {"redirects": "./data/redirects.json"},
                },
                {},
                "normalized",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                    "dataFiles": {"redirects": "data//redirects.json"},
                },
                {},
                "normalized",
            ),
            (
                {
                    "schemaVersion": 1,
                    "stageLayoutVersion": 1,
                    "aggregateFormat": "json",
                    "dataFiles": {"redirects": "data/./redirects.json"},
                },
                {},
                "normalized",
            ),
        )
        for manifest, aggregate, expected in cases:
            with (
                self.subTest(expected=expected),
                tempfile.TemporaryDirectory() as tempdir,
            ):
                stage_root = Path(tempdir) / "stage"
                stage_root.mkdir()
                (stage_root / "manifest.json").write_text(
                    json.dumps(manifest) + "\n", encoding="utf-8"
                )
                (stage_root / "outside.json").write_text(
                    json.dumps(aggregate) + "\n", encoding="utf-8"
                )

                with self.assertRaisesRegex(AdapterError, expected):
                    render_apache_redirects(
                        stage_root=stage_root,
                        source_origin="https://docs.example.org",
                    )

        aggregate_cases = (
            ([], "JSON object"),
            ({"items": {}, "extra": True}, "only an items field"),
            ({"items": {}}, "items must be an array"),
            ({"items": [None]}, "item 0 must be an object"),
            ({"items": [{"fromUrl": "https://docs.example.org/old/"}]}, "missing"),
            (
                {
                    "items": [
                        {**_redirect("https://docs.example.org/old/"), "extra": True}
                    ]
                },
                "unknown fields",
            ),
        )
        for aggregate, expected in aggregate_cases:
            with (
                self.subTest(expected=expected),
                tempfile.TemporaryDirectory() as tempdir,
            ):
                stage_root = Path(tempdir) / "stage"
                _create_stage(stage_root, [])
                (stage_root / "data/redirects.json").write_text(
                    json.dumps(aggregate) + "\n", encoding="utf-8"
                )

                with self.assertRaisesRegex(AdapterError, expected):
                    render_apache_redirects(
                        stage_root=stage_root,
                        source_origin="https://docs.example.org",
                    )

        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            _create_stage(stage_root, [])
            (stage_root / "data/redirects.json").write_text(
                '{"items": [], "items": []}\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(AdapterError, "duplicate JSON key"):
                render_apache_redirects(
                    stage_root=stage_root,
                    source_origin="https://docs.example.org",
                )

    def test_rejects_unsupported_status_origin_and_source_paths(self) -> None:
        cases = (
            ({**_redirect("https://docs.example.org/old/"), "status": 303}, "status"),
            ({**_redirect("https://docs.example.org/old/"), "status": True}, "status"),
            (_redirect("https://docs.example.org/old/?query=yes"), "query or fragment"),
            (_redirect("https://docs.example.org/old%20page/"), "unescaped ASCII"),
            (_redirect("https://docs.example.org/double//slash/"), "normalized"),
        )
        for item, expected in cases:
            with self.subTest(item=item), tempfile.TemporaryDirectory() as tempdir:
                stage_root = Path(tempdir) / "stage"
                _create_stage(stage_root, [item])

                with self.assertRaisesRegex(AdapterError, expected):
                    render_apache_redirects(
                        stage_root=stage_root,
                        source_origin="https://docs.example.org",
                    )

        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            _create_stage(stage_root, [_redirect("https://other.example.org/old/")])
            with self.assertRaisesRegex(AdapterError, "no redirects for source origin"):
                render_apache_redirects(
                    stage_root=stage_root,
                    source_origin="https://docs.example.org",
                )
            with self.assertRaisesRegex(AdapterError, "must not contain whitespace"):
                render_apache_redirects(
                    stage_root=stage_root,
                    source_origin="bad host",
                )
            with self.assertRaisesRegex(AdapterError, "only scheme, host"):
                render_apache_redirects(
                    stage_root=stage_root,
                    source_origin="https://docs.example.org/not-an-origin",
                )

    def test_rejects_apache_config_expansion_and_injection_syntax(self) -> None:
        destinations = (
            'https://new.example.org/"\nRewriteRule bad injected',
            "https://new.example.org/back\\slash/",
            "https://new.example.org/$1/",
            "https://new.example.org/${map:key}/",
            "https://new.example.org/%1/",
            "https://new.example.org/%{HTTP_HOST}/",
        )
        for destination in destinations:
            with (
                self.subTest(destination=destination),
                tempfile.TemporaryDirectory() as tempdir,
            ):
                stage_root = Path(tempdir) / "stage"
                _create_stage(
                    stage_root,
                    [_redirect("https://docs.example.org/old/", to_url=destination)],
                )

                with self.assertRaises(AdapterError):
                    render_apache_redirects(
                        stage_root=stage_root,
                        source_origin="https://docs.example.org",
                    )

        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            _create_stage(
                stage_root,
                [_redirect('https://docs.example.org/injected"rule/')],
            )
            with self.assertRaisesRegex(AdapterError, "change an Apache rule"):
                render_apache_redirects(
                    stage_root=stage_root,
                    source_origin="https://docs.example.org",
                )

    def test_rejects_duplicate_sources_and_does_not_overwrite_on_failure(self) -> None:
        duplicate = _redirect("https://docs.example.org/old/")
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stage_root = root / "stage"
            output_path = root / "redirects.conf"
            output_path.write_text("existing\n", encoding="utf-8")
            _create_stage(stage_root, [duplicate, duplicate])

            with self.assertRaisesRegex(AdapterError, "duplicate source"):
                write_apache_redirects(
                    stage_root=stage_root,
                    source_origin="https://docs.example.org",
                    output_path=output_path,
                )

            self.assertEqual("existing\n", output_path.read_text(encoding="utf-8"))


def _redirect(
    from_url: str,
    *,
    status: int = 302,
    to_url: str | None = None,
) -> dict[str, object]:
    path = from_url.split(".org", maxsplit=1)[-1]
    return {
        "fromUrl": from_url,
        "toUrl": to_url or f"https://new.example.org{path}?source=old#start",
        "status": status,
        "reason": "The old route moved.",
        "sourceKind": "catalog",
    }


def _create_stage(
    stage_root: Path,
    items: list[dict[str, object]],
    *,
    redirects_path: str = "data/redirects.json",
) -> None:
    stage_root.mkdir(parents=True)
    aggregate_path = stage_root.joinpath(*redirects_path.split("/"))
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    (stage_root / "manifest.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "stageLayoutVersion": 1,
                "aggregateFormat": "json",
                "dataFiles": {"redirects": redirects_path},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    aggregate_path.write_text(json.dumps({"items": items}) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
