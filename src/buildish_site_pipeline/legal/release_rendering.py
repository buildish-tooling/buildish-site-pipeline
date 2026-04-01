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

"""Render preliminary release-legal LICENSE, NOTICE, and inventory text."""

from __future__ import annotations

from .release_models import CapturedLegalFile, DistributionInventoryEntry, ReleaseLegalReport

_REPOSITORY_URL_LABELS = {"repository", "source", "github"}
_PRELIMINARY_WARNING = (
    "This file is PRELIMINARY and generated from dependency metadata plus "
    "bundled legal files. Human review is required before using it in any "
    "published release artifact."
)
_LICENSE_SECTION_INTRO = (
    "The sections below describe bundled third-party Python runtime dependencies "
    "selected from uv.lock and inspected from the current installed environment."
)
_NOTICE_SECTION_INTRO = (
    "The sections below reproduce bundled third-party NOTICE-like content for "
    "human review."
)


def build_preliminary_license_text(
    report: ReleaseLegalReport, project_license_text: str
) -> str:
    """Render the generated draft ``LICENSE`` text."""

    lines = [_ensure_trailing_newline(project_license_text).rstrip("\n"), ""]
    if not report.bundled_entries:
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(
        [
            _section_rule(),
            _LICENSE_SECTION_INTRO,
            _PRELIMINARY_WARNING,
            f"Selection command: {' '.join(report.selection_command)}",
            "",
        ]
    )
    for entry in report.bundled_entries:
        lines.extend(
            _render_license_distribution_section(
                entry,
                project_license_text=project_license_text,
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def build_preliminary_notice_text(
    report: ReleaseLegalReport, project_notice_text: str
) -> str:
    """Render the generated draft ``NOTICE`` text."""

    lines = [_ensure_trailing_newline(project_notice_text).rstrip("\n"), ""]
    entries_with_notices = tuple(
        entry for entry in report.bundled_entries if entry.notice_files
    )
    if not entries_with_notices:
        return "\n".join(lines).rstrip() + "\n"
    lines.extend(
        [
            _section_rule(),
            _NOTICE_SECTION_INTRO,
            _PRELIMINARY_WARNING,
            f"Selection command: {' '.join(report.selection_command)}",
            "",
        ]
    )
    for entry in entries_with_notices:
        lines.extend(_render_notice_distribution_section(entry))
    return "\n".join(lines).rstrip() + "\n"


def build_inventory_markdown(report: ReleaseLegalReport) -> str:
    """Render the human-readable Markdown inventory."""

    packages_with_notices = sum(1 for entry in report.entries if entry.notice_files)
    packages_with_flags = sum(1 for entry in report.entries if entry.review_flags)
    lines = [
        "<!--",
        "Copyright 2026 The Buildish Authors",
        "",
        'Licensed under the Apache License, Version 2.0 (the "License");',
        "you may not use this file except in compliance with the License.",
        "You may obtain a copy of the License at",
        "",
        "http://www.apache.org/licenses/LICENSE-2.0",
        "",
        "Unless required by applicable law or agreed to in writing, software",
        'distributed under the License is distributed on an "AS IS" BASIS,',
        "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
        "See the License for the specific language governing permissions and",
        "limitations under the License.",
        "-->",
        "",
        "# Preliminary release-legal inventory",
        "",
        _PRELIMINARY_WARNING,
        "",
        f"- selection command: `{' '.join(report.selection_command)}`",
        f"- runtime packages: `{len(report.python_runtime_entries)}`",
        f"- supplemental bundled components: `{len(report.supplemental_entries)}`",
        f"- packages with bundled notice files: `{packages_with_notices}`",
        f"- packages with review flags: `{packages_with_flags}`",
        "",
        "## Package summary",
        "",
        "| Package | Source | Declared license | License files | Notice files | Review flags |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in report.entries:
        flags = ", ".join(entry.review_flags) if entry.review_flags else "—"
        lines.append(
            "| "
            f"`{entry.name}` | `{entry.source_kind}` | "
            f"{_escape_markdown_table_cell(entry.declared_license_summary or '(missing)')} | "
            f"{len(entry.license_files)} | {len(entry.notice_files)} | "
            f"{_escape_markdown_table_cell(flags)} |"
        )
    lines.extend(["", "## Review details", ""])
    for entry in report.entries:
        lines.extend(_render_inventory_detail_section(entry))
    return "\n".join(lines).rstrip() + "\n"


def _render_license_distribution_section(
    entry: DistributionInventoryEntry,
    *,
    project_license_text: str,
) -> list[str]:
    lines = [_section_rule(), f"This product bundles {entry.name}.", ""]
    for link_label, url in _license_section_links(entry):
        lines.append(f"{link_label}: {url}")
    lines.append(f"License: {_display_license_name(entry)}")
    review_notes = _review_note_messages(entry.review_flags)
    if review_notes:
        lines.append("Review notes:")
        lines.extend(f"* {review_note}" for review_note in review_notes)
    lines.append("")
    for legal_file in entry.license_files:
        if _should_inline_license_text(
            entry,
            legal_file=legal_file,
            project_license_text=project_license_text,
        ):
            lines.append(
                f"Included license text from {legal_file.output_relative_path}:"
            )
            lines.extend(_pipe_prefixed_lines(legal_file.text))
            lines.append("")
    return lines


def _render_notice_distribution_section(entry: DistributionInventoryEntry) -> list[str]:
    lines = [
        _section_rule(),
        f"This product bundles {entry.name} with the following in its NOTICE file:",
        "|",
    ]
    for legal_file in entry.notice_files:
        lines.extend(_pipe_prefixed_lines(legal_file.text))
        lines.append("|")
    lines.append("")
    return lines


def _license_section_links(entry: DistributionInventoryEntry) -> tuple[tuple[str, str], ...]:
    links: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    if entry.home_page is not None:
        links.append(("Project URL", entry.home_page))
        seen_urls.add(entry.home_page)
    for project_url in entry.project_urls:
        if project_url.label.strip().lower() not in _REPOSITORY_URL_LABELS:
            continue
        if project_url.url in seen_urls:
            continue
        links.append(("Repository URL", project_url.url))
        break
    return tuple(links)


def _review_note_messages(review_flags: tuple[str, ...]) -> tuple[str, ...]:
    messages = (_review_note_message(flag) for flag in review_flags)
    return tuple(message for message in messages if message is not None)


def _review_note_message(review_flag: str) -> str | None:
    messages = {
        "missing-license-metadata": (
            "The package metadata does not declare a license. Review the bundled "
            "legal files manually before relying on this entry."
        ),
        "license-and-license-expression-both-present": (
            "The package declares both `License` and `License-Expression` metadata. "
            "Verify that both declarations agree."
        ),
        "no-license-files-detected": (
            "No bundled license file was detected in the installed distribution. "
            "Check whether a license file still needs to be added manually."
        ),
        "bundled-notice-files-require-review": (
            "A bundled NOTICE-like file was detected. Review whether its contents "
            "must be merged into the final `NOTICE`."
        ),
        "legal-file-utf8-decode-warning": (
            "At least one captured legal file was not valid UTF-8 and was decoded "
            "with replacement characters. Verify the copied text manually."
        ),
        "missing-curated-license-files": (
            "This curated container-image entry does not list any license files yet. "
            "Add them before relying on this output."
        ),
    }
    if review_flag == "classifier-only-license-metadata":
        return None
    return messages.get(review_flag, f"Manual review is required for `{review_flag}`.")


def _render_inventory_detail_section(entry: DistributionInventoryEntry) -> list[str]:
    lines = [f"### {entry.name}", ""]
    lines.append(
        f"- source: `{entry.source_kind}`"
        f"{_markdown_source_reference_suffix(entry.source_reference)}"
    )
    lines.append(
        "- declared license: "
        f"`{entry.declared_license_summary or '(missing declared license metadata)'}`"
    )
    if entry.home_page is not None:
        lines.append(f"- home page: `{entry.home_page}`")
    if entry.project_urls:
        lines.append("- project URLs:")
        lines.extend(
            f"  - `{project_url.label}`: `{project_url.url}`"
            for project_url in entry.project_urls
        )
    if entry.requires_dist:
        lines.append("- Requires-Dist entries:")
        lines.extend(f"  - `{requirement}`" for requirement in entry.requires_dist)
    _append_file_inventory(lines, "copied license files", entry.license_files)
    _append_file_inventory(lines, "copied notice files", entry.notice_files)
    lines.append("- review flags:")
    lines.extend(
        (f"  - `{flag}`" for flag in entry.review_flags)
        if entry.review_flags
        else ("  - none",)
    )
    lines.append("")
    return lines


def _append_file_inventory(
    lines: list[str],
    heading: str,
    files: tuple[CapturedLegalFile, ...],
) -> None:
    lines.append(f"- {heading}:")
    lines.extend(
        (f"  - `{legal_file.output_relative_path}`" for legal_file in files)
        if files
        else ("  - none found",)
    )


def _escape_markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _section_rule() -> str:
    return "-" * 79


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else f"{text}\n"


def _markdown_source_reference_suffix(source_reference: str | None) -> str:
    return "" if source_reference is None else f" (`{source_reference}`)"


def _display_license_name(entry: DistributionInventoryEntry) -> str:
    if entry.license_expression is not None:
        return entry.license_expression
    if entry.license_field is not None:
        return entry.license_field
    if entry.license_classifiers:
        return "; ".join(entry.license_classifiers)
    return "(missing declared license metadata)"


def _should_inline_license_text(
    entry: DistributionInventoryEntry,
    *,
    legal_file: CapturedLegalFile,
    project_license_text: str,
) -> bool:
    return (
        entry.license_expression != "Apache-2.0"
        and legal_file.text.strip() != project_license_text.strip()
    )


def _pipe_prefixed_lines(text: str) -> list[str]:
    return [f"| {line}" if line else "|" for line in text.rstrip("\n").splitlines()]
