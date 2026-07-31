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

"""Generate origin-scoped Apache httpd redirects from one completed stage.

This reference adapter deliberately supports a conservative subset of URL
paths and destinations. Failing on syntax that could change ``mod_rewrite``
parsing is safer than emitting a rule with different behavior from the staged
redirect contract.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import SplitResult, urlsplit


_ALLOWED_STATUSES = frozenset({301, 302, 307, 308})
_ENTRY_KEYS = frozenset({"fromUrl", "toUrl", "status", "reason", "sourceKind"})
_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")
_REWRITE_EXPANSION = re.compile(r'(?:[\\"]|\$(?:[0-9]|\{)|%(?:[0-9]|\{))')


class AdapterError(RuntimeError):
    """Report staged metadata that cannot be represented safely by this adapter."""


@dataclass(frozen=True, slots=True)
class SourceOrigin:
    """Normalized source origin used for selection and request guards."""

    scheme: str
    host: str
    port: int


@dataclass(frozen=True, slots=True)
class Redirect:
    """One validated redirect ready for deterministic Apache rendering."""

    origin: SourceOrigin
    path: str
    destination: str
    status: int


def render_apache_redirects(*, stage_root: Path, source_origin: str) -> str:
    """Render exact-match rules for one source origin from a completed stage."""

    normalized_origin = _parse_source_origin(
        source_origin, label="target source origin"
    )
    redirects = _load_redirects(stage_root)
    selected = sorted(
        (redirect for redirect in redirects if redirect.origin == normalized_origin),
        key=lambda redirect: (
            redirect.path,
            redirect.status,
            redirect.destination,
        ),
    )
    if not selected:
        raise AdapterError(
            "staged metadata contains no redirects for source origin "
            f"{_format_origin(normalized_origin)!r}"
        )

    host_pattern = _host_pattern(normalized_origin)
    https_pattern = "^on$" if normalized_origin.scheme == "https" else "!^on$"
    lines = [
        "# Generated from Site Pipeline staged redirect metadata.",
        f"# Target source origin: {_format_origin(normalized_origin)}",
        "# Include in server or VirtualHost context; do not use in .htaccess.",
        "RewriteEngine On",
        "",
    ]
    for redirect in selected:
        source_pattern = re.escape(redirect.path)
        rule_line = (
            f'RewriteRule "^{source_pattern}$" "{redirect.destination}" '
            f"[R={redirect.status},L,NE,QSD]"
        )
        lines.extend(
            (
                f'RewriteCond "%{{HTTPS}}" "{https_pattern}" [NC]',
                f'RewriteCond "%{{HTTP_HOST}}" "^{host_pattern}$" [NC]',
                rule_line,
                "",
            )
        )
    return "\n".join(lines)


def write_apache_redirects(
    *, stage_root: Path, source_origin: str, output_path: Path
) -> None:
    """Write one validated Apache snippet, refusing a symlinked output file."""

    rendered = render_apache_redirects(
        stage_root=stage_root, source_origin=source_origin
    )
    if output_path.is_symlink():
        raise AdapterError(f"output path must not be a symlink: {output_path}")
    try:
        output_path.write_text(rendered, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AdapterError(f"could not write Apache config: {exc}") from exc


def _load_redirects(stage_root: Path) -> tuple[Redirect, ...]:
    stage_root = stage_root.absolute()
    if stage_root.is_symlink() or not stage_root.is_dir():
        raise AdapterError(f"stage root must be an ordinary directory: {stage_root}")

    manifest_path = stage_root / "manifest.json"
    manifest = _load_json_object(manifest_path, label="stage manifest")
    if type(manifest.get("schemaVersion")) is not int or manifest["schemaVersion"] != 1:
        raise AdapterError(
            "reference adapter supports only stage manifest schema version 1"
        )
    if (
        type(manifest.get("stageLayoutVersion")) is not int
        or manifest["stageLayoutVersion"] != 1
    ):
        raise AdapterError("reference adapter supports only stage layout version 1")
    if manifest.get("aggregateFormat") != "json":
        raise AdapterError("reference adapter supports only JSON aggregate files")

    data_files = manifest.get("dataFiles")
    if not isinstance(data_files, Mapping):
        raise AdapterError("stage manifest must declare dataFiles as an object")
    redirect_path = _safe_stage_path(data_files.get("redirects"))
    aggregate_path = stage_root.joinpath(*redirect_path.parts)
    _reject_symlink_components(stage_root=stage_root, path=aggregate_path)
    aggregate = _load_json_object(aggregate_path, label="redirect aggregate")
    if set(aggregate) != {"items"}:
        raise AdapterError("redirect aggregate must contain only an items field")
    items = aggregate["items"]
    if not isinstance(items, list):
        raise AdapterError("redirect aggregate items must be an array")

    redirects = tuple(
        _parse_redirect(item, index=index) for index, item in enumerate(items)
    )
    _reject_duplicate_sources(redirects)
    return redirects


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise AdapterError(f"{label} must be an ordinary file: {path}")
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=lambda pairs: _object_without_duplicate_keys(
                pairs, label=label
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"cannot read {label}: {exc}") from exc
    if not isinstance(document, dict):
        raise AdapterError(f"{label} must be a JSON object")
    return document


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]], *, label: str
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdapterError(f"{label} contains duplicate JSON key {key!r}")
        result[key] = value
    return result


def _safe_stage_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AdapterError("manifest dataFiles.redirects must be a POSIX path string")
    raw_parts = value.split("/")
    if value.startswith("/") or ".." in raw_parts:
        raise AdapterError("manifest dataFiles.redirects must be stage-relative")
    if any(part in {"", "."} for part in raw_parts):
        raise AdapterError("manifest dataFiles.redirects must be normalized")
    return PurePosixPath(value)


def _reject_symlink_components(*, stage_root: Path, path: Path) -> None:
    current = stage_root
    for part in path.relative_to(stage_root).parts:
        current /= part
        if current.is_symlink():
            raise AdapterError(
                f"redirect aggregate path must not contain symlinks: {current}"
            )


def _parse_redirect(value: Any, *, index: int) -> Redirect:
    label = f"redirect item {index}"
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be an object")
    keys = set(value)
    missing = {"fromUrl", "toUrl", "status"} - keys
    unknown = keys - _ENTRY_KEYS
    if missing:
        raise AdapterError(f"{label} is missing: {', '.join(sorted(missing))}")
    if unknown:
        raise AdapterError(f"{label} has unknown fields: {', '.join(sorted(unknown))}")
    for optional_key in ("reason", "sourceKind"):
        optional_value = value.get(optional_key)
        if optional_value is not None and (
            not isinstance(optional_value, str) or not optional_value
        ):
            raise AdapterError(
                f"{label}.{optional_key} must be a non-empty string or null"
            )

    status = value["status"]
    if type(status) is not int or status not in _ALLOWED_STATUSES:
        raise AdapterError(f"{label}.status must be one of 301, 302, 307, or 308")
    source = _parse_url(value["fromUrl"], label=f"{label}.fromUrl")
    destination_text = value["toUrl"]
    if not isinstance(destination_text, str):
        raise AdapterError(f"{label}.toUrl must be a non-empty URL string")
    _parse_url(destination_text, label=f"{label}.toUrl")
    if source.query or source.fragment:
        raise AdapterError(f"{label}.fromUrl must not contain a query or fragment")
    _validate_source_path(source.path, label=f"{label}.fromUrl path")

    if _REWRITE_EXPANSION.search(destination_text):
        raise AdapterError(
            f"{label}.toUrl contains syntax that could expand in an Apache rule"
        )
    return Redirect(
        origin=_origin_from_parsed_url(source, label=f"{label}.fromUrl"),
        path=source.path,
        destination=destination_text,
        status=status,
    )


def _parse_url(value: Any, *, label: str) -> SplitResult:
    if not isinstance(value, str) or not value:
        raise AdapterError(f"{label} must be a non-empty URL string")
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise AdapterError(f"{label} must not contain whitespace or control characters")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise AdapterError(f"{label} is not a valid absolute URL: {exc}") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AdapterError(f"{label} must be an absolute HTTP or HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise AdapterError(f"{label} must not contain user information")
    if parsed.hostname is None:
        raise AdapterError(f"{label} must contain a hostname")
    _normalize_host(parsed.hostname, label=f"{label} host")
    if port is not None and not 1 <= port <= 65535:
        raise AdapterError(f"{label} contains an invalid port")
    return parsed


def _parse_source_origin(value: str, *, label: str) -> SourceOrigin:
    parsed = _parse_url(value, label=label)
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise AdapterError(f"{label} must contain only scheme, host, and optional port")
    return _origin_from_parsed_url(parsed, label=label)


def _origin_from_parsed_url(parsed: SplitResult, *, label: str) -> SourceOrigin:
    scheme = parsed.scheme
    default_port = 443 if scheme == "https" else 80
    return SourceOrigin(
        scheme=scheme,
        host=_normalize_host(parsed.hostname or "", label=f"{label} host"),
        port=parsed.port or default_port,
    )


def _format_origin(origin: SourceOrigin) -> str:
    default_port = 443 if origin.scheme == "https" else 80
    port_suffix = "" if origin.port == default_port else f":{origin.port}"
    return f"{origin.scheme}://{origin.host}{port_suffix}"


def _host_pattern(origin: SourceOrigin) -> str:
    escaped_host = re.escape(origin.host)
    default_port = 443 if origin.scheme == "https" else 80
    if origin.port == default_port:
        return f"{escaped_host}(?::{default_port})?"
    return f"{escaped_host}:{origin.port}"


def _validate_source_path(value: str, *, label: str) -> None:
    if not value.startswith("/"):
        raise AdapterError(f"{label} must be an absolute URL path")
    if '"' in value or "\\" in value:
        raise AdapterError(f"{label} contains syntax that could change an Apache rule")
    if "%" in value or not value.isascii():
        raise AdapterError(
            f"{label} must use unescaped ASCII so Apache matches it exactly"
        )
    normalized = value[:-1] if value != "/" and value.endswith("/") else value
    if normalized != "/" and any(
        part in {"", ".", ".."} for part in normalized[1:].split("/")
    ):
        raise AdapterError(f"{label} must be normalized and traversal-free")


def _normalize_host(value: str, *, label: str) -> str:
    if not value or not value.isascii() or len(value) > 253:
        raise AdapterError(f"{label} must be an ASCII DNS hostname")
    labels = value.rstrip(".").split(".")
    if any(len(part) > 63 or _HOST_LABEL.fullmatch(part) is None for part in labels):
        raise AdapterError(f"{label} must be an ASCII DNS hostname without a port")
    return ".".join(part.lower() for part in labels)


def _reject_duplicate_sources(redirects: tuple[Redirect, ...]) -> None:
    seen: set[tuple[SourceOrigin, str]] = set()
    for redirect in redirects:
        source = (redirect.origin, redirect.path)
        if source in seen:
            raise AdapterError(
                "redirect aggregate contains duplicate source "
                f"{_format_origin(redirect.origin)}{redirect.path}"
            )
        seen.add(source)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate exact-match Apache redirects from a completed stage."
    )
    parser.add_argument("stage_root", type=Path, help="completed Site Pipeline stage")
    parser.add_argument(
        "source_origin",
        help="HTTP(S) source origin whose redirects should be emitted",
    )
    parser.add_argument("output", type=Path, help="Apache config file to write")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the copyable Apache adapter command."""

    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        write_apache_redirects(
            stage_root=arguments.stage_root,
            source_origin=arguments.source_origin,
            output_path=arguments.output,
        )
    except AdapterError as exc:
        parser.exit(status=1, message=f"{parser.prog}: error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
