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

"""Generate the checked-in Markdown reference for public pipeline models."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from inspect import cleandoc, getdoc
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any, get_args, get_origin

import yaml

from apache_buildish_site_pipeline.models.base import SitePipelineBaseModel, to_camel_case
from apache_buildish_site_pipeline.models.documentation import contract_documentation_for
from apache_buildish_site_pipeline.models.reference_docs import ReferenceDocError, TypeReferenceTarget
from apache_buildish_site_pipeline.models.reference_docs.registry import (
    MODEL_SECTION_DEFINITIONS,
    SCALAR_REFERENCE_ENTRIES,
    ModelSectionDefinition,
    ScalarReferenceEntry,
)

if TYPE_CHECKING:
    from apache_buildish_site_pipeline.schema_export import SchemaExport
    from apache_buildish_site_pipeline.schema_export import SchemaExample

_GENERATED_REFERENCE_COMMENT = (
    "Generated from the Site Pipeline Pydantic models and checked-in reference metadata. "
    "Do not edit by hand; regenerate with `make schemas`."
)
_TOKEN_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


@dataclass(frozen=True, slots=True)
class AnchorIndex:
    """Stable generated anchors for types, scalars, enums, and fields."""

    type_anchors: dict[str, str]
    field_anchors: dict[tuple[str, str], str]

    def resolve_type_target(self, target: TypeReferenceTarget) -> str:
        type_anchor = self.type_anchors.get(target.type_name)
        if type_anchor is None:
            raise ReferenceDocError(f"Unknown generated reference type target: {target.type_name!r}")
        if target.field_name is None:
            return f"#{type_anchor}"
        field_anchor = self.field_anchors.get((target.type_name, target.field_name))
        if field_anchor is None:
            raise ReferenceDocError(
                f"Unknown generated reference field target: {target.type_name}#{target.field_name}",
            )
        return f"#{field_anchor}"

    def link_type_expression(self, expression: str) -> str:
        return _TOKEN_PATTERN.sub(self._replace_type_token, expression)

    def _replace_type_token(self, match: re.Match[str]) -> str:
        token = match.group(0)
        anchor = self.type_anchors.get(token)
        return token if anchor is None else f"[{token}](#{anchor})"


def build_reference_markdown(exports: Iterable[SchemaExport]) -> str:
    """Build the generated Markdown schema reference from public model metadata."""

    export_list = tuple(exports)
    reachable_models = _collect_reachable_models(export_list)
    reachable_enums = _collect_reachable_enums(reachable_models)
    anchors = _build_anchor_index(reachable_models, reachable_enums, SCALAR_REFERENCE_ENTRIES)
    examples_by_root = _examples_by_root_model(export_list)

    lines = [
        "---",
        "weight: 30",
        "---",
        "",
        "<!--",
        "Copyright 2026 The Apache Software Foundation",
        "",
        "Licensed under the Apache License, Version 2.0 (the \"License\");",
        "you may not use this file except in compliance with the License.",
        "You may obtain a copy of the License at",
        "",
        "http://www.apache.org/licenses/LICENSE-2.0",
        "",
        "Unless required by applicable law or agreed to in writing, software",
        "distributed under the License is distributed on an \"AS IS\" BASIS,",
        "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
        "See the License for the specific language governing permissions and",
        "limitations under the License.",
        "-->",
        "",
        "# Pipeline model schema reference",
        "",
        _GENERATED_REFERENCE_COMMENT,
        "",
        "This page is generated from the public model layer and the checked-in schema export registry.",
        "It is the typed reference companion to the narrative maintenance and how-to docs.",
        "",
        "## Scope and conventions",
        "",
        "- field names are shown in their wire-format aliases",
        "- field type expressions use Python-style annotations because they are generated from the actual model signatures",
        "- type, enum, and scalar names link to anchors in this document",
        "- schema-file links point to the checked-in generated JSON Schema files under `/schemas/`",
        "",
    ]
    lines.extend(_render_file_contract_index(export_list, anchors))
    lines.extend(_render_scalar_section())
    lines.extend(_render_enum_section(reachable_enums, anchors))
    lines.extend(_render_model_index(reachable_models, anchors))
    lines.extend(_render_model_sections(reachable_models, anchors, examples_by_root))
    return "\n".join(lines) + "\n"


def write_reference_markdown_file(output_path: Path, exports: Iterable[SchemaExport]) -> Path:
    """Write the generated Markdown model reference to ``output_path``."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_reference_markdown(exports), encoding="utf-8")
    return output_path


def _collect_reachable_models(exports: tuple[SchemaExport, ...]) -> tuple[type[SitePipelineBaseModel], ...]:
    seen: set[type[SitePipelineBaseModel]] = set()

    def collect(model: type[SitePipelineBaseModel]) -> None:
        if model in seen:
            return
        seen.add(model)
        for field in model.model_fields.values():
            _walk_annotation(field.annotation, collect_model=collect, collect_enum=lambda _: None)

    for export in exports:
        for root in export.reference_roots:
            collect(root)
    return tuple(sorted(seen, key=lambda model: (model.__module__, model.__name__)))


def _collect_reachable_enums(
    models: tuple[type[SitePipelineBaseModel], ...],
) -> tuple[type[Enum], ...]:
    seen: set[type[Enum]] = set()
    for model in models:
        for field in model.model_fields.values():
            _walk_annotation(field.annotation, collect_model=lambda _: None, collect_enum=seen.add)
    return tuple(sorted(seen, key=lambda enum_type: enum_type.__name__))


def _walk_annotation(
    annotation: Any,
    *,
    collect_model: Callable[[type[SitePipelineBaseModel]], None],
    collect_enum: Callable[[type[Enum]], None],
) -> None:
    origin = get_origin(annotation)
    if origin is None:
        if isinstance(annotation, type):
            if issubclass(annotation, SitePipelineBaseModel):
                collect_model(annotation)
            elif issubclass(annotation, Enum):
                collect_enum(annotation)
        return
    for argument in get_args(annotation):
        if argument is type(None):
            continue
        _walk_annotation(argument, collect_model=collect_model, collect_enum=collect_enum)


def _build_anchor_index(
    models: tuple[type[SitePipelineBaseModel], ...],
    enums: tuple[type[Enum], ...],
    scalar_entries: tuple[ScalarReferenceEntry, ...],
) -> AnchorIndex:
    type_anchors: dict[str, str] = {}
    field_anchors: dict[tuple[str, str], str] = {}
    for scalar in scalar_entries:
        type_anchors[scalar.name] = _slugify_anchor(scalar.name)
    for enum_type in enums:
        type_anchors[enum_type.__name__] = _slugify_anchor(enum_type.__name__)
    for model in models:
        type_anchors[model.__name__] = _slugify_anchor(model.__name__)
        for field_name, field in model.model_fields.items():
            alias = field.alias or to_camel_case(field_name)
            anchor = f"{type_anchors[model.__name__]}-{_slugify_anchor(alias)}"
            field_anchors[(model.__name__, alias)] = anchor
            field_anchors[(model.__name__, field_name)] = anchor
    return AnchorIndex(type_anchors=type_anchors, field_anchors=field_anchors)


def _slugify_anchor(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _render_file_contract_index(exports: tuple[SchemaExport, ...], anchors: AnchorIndex) -> list[str]:
    lines = [
        "## File contract index",
        "",
        "| Schema file | Contract file | Root type(s) | Ownership | Summary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for export in exports:
        documentation = export.documentation
        summary = documentation.summary if documentation is not None and documentation.summary is not None else export.description or "—"
        ownership = documentation.ownership if documentation is not None else "—"
        file_path = documentation.file_path if documentation is not None and documentation.file_path is not None else "—"
        root_types = ", ".join(
            f"[{root.__name__}](#{anchors.type_anchors[root.__name__]})" for root in export.reference_roots
        ) or "—"
        lines.append(
            f"| [{export.filename}](/schemas/{export.filename}) | `{file_path}` | {root_types} | {ownership} | {_escape_table_cell(summary)} |"
        )
    lines.extend(["", ""]) 
    return lines


def _render_scalar_section() -> list[str]:
    lines = [
        "## Scalar aliases",
        "",
        "| Type | Base type | Description |",
        "| --- | --- | --- |",
    ]
    for entry in SCALAR_REFERENCE_ENTRIES:
        anchor = _slugify_anchor(entry.name)
        lines.append(
            f"| <a id=\"{anchor}\"></a>`{entry.name}` | `{entry.base_type}` | {_escape_table_cell(entry.description)} |"
        )
    lines.extend(["", ""]) 
    return lines


def _render_enum_section(enums: tuple[type[Enum], ...], anchors: AnchorIndex) -> list[str]:
    lines = [
        "## Shared enums",
        "",
        "| Type | Values | Description |",
        "| --- | --- | --- |",
    ]
    for enum_type in enums:
        anchor = anchors.type_anchors[enum_type.__name__]
        values = ", ".join(f"`{member.value}`" for member in enum_type)
        description = getdoc(enum_type) or "—"
        lines.append(
            f"| <a id=\"{anchor}\"></a>`{enum_type.__name__}` | {values} | {_escape_table_cell(description)} |"
        )
    lines.extend(["", ""]) 
    return lines


def _render_model_index(models: tuple[type[SitePipelineBaseModel], ...], anchors: AnchorIndex) -> list[str]:
    lines = ["## Type index", ""]
    grouped = _group_models(models)
    for definition, grouped_models in grouped:
        lines.append(f"### {definition.title}")
        lines.append("")
        lines.append(definition.description)
        lines.append("")
        for model in grouped_models:
            lines.append(f"- [{model.__name__}](#{anchors.type_anchors[model.__name__]})")
        lines.append("")
    return lines


def _render_model_sections(
    models: tuple[type[SitePipelineBaseModel], ...],
    anchors: AnchorIndex,
    examples_by_root: dict[type[SitePipelineBaseModel], tuple[SchemaExample, ...]],
) -> list[str]:
    lines: list[str] = []
    for definition, grouped_models in _group_models(models):
        lines.append(f"## {definition.title}")
        lines.append("")
        lines.append(definition.description)
        lines.append("")
        for model in grouped_models:
            lines.extend(_render_model_section(model, anchors, examples_by_root.get(model, ())))
    return lines


def _render_model_section(
    model: type[SitePipelineBaseModel],
    anchors: AnchorIndex,
    examples: tuple[SchemaExample, ...],
) -> list[str]:
    documentation = contract_documentation_for(model)
    summary_source = (
        documentation.reference.summary.source
        if documentation is not None and documentation.reference is not None and documentation.reference.summary is not None
        else getdoc(model) or "No model summary documented."
    )
    lines = [
        f"<a id=\"{anchors.type_anchors[model.__name__]}\"></a>",
        f"### {model.__name__}",
        "",
        _render_markdown_fragment(summary_source, anchors),
        "",
    ]
    if documentation is not None:
        lines.extend(
            [
                "- category: `{}`".format(documentation.category),
                "- ownership: `{}`".format(documentation.ownership),
                "- file contract: `{}`".format(documentation.file_path)
                if documentation.file_path is not None
                else "- file contract: —",
                "",
            ]
        )
    lines.extend(
        [
            "| Field | Type | Required | Description |",
            "| --- | --- | --- | --- |",
        ]
    )
    for field_name, field in model.model_fields.items():
        alias = field.alias or to_camel_case(field_name)
        field_anchor = anchors.field_anchors[(model.__name__, alias)]
        raw_type = model.__annotations__.get(field_name, repr(field.annotation))
        rendered_type = anchors.link_type_expression(str(raw_type))
        description = field.description or "—"
        lines.append(
            f"| <a id=\"{field_anchor}\"></a>`{alias}` | {_escape_table_cell(rendered_type)} | {'yes' if field.is_required() else 'no'} | {_escape_table_cell(_render_markdown_fragment(description, anchors) if description != '—' else description)} |"
        )
    lines.append("")
    if documentation is not None and documentation.reference is not None:
        for section in documentation.reference.sections:
            lines.append(f"#### {section.title}")
            lines.append("")
            lines.append(_render_markdown_fragment(section.body.source, anchors))
            lines.append("")
    for example in examples:
        lines.append(f"#### Example: {example.summary}")
        lines.append("")
        lines.append(_render_example_block(example))
        lines.append("")
    return lines


def _render_markdown_fragment(source: str, anchors: AnchorIndex) -> str:
    from apache_buildish_site_pipeline.models.reference_docs import parse_reference_document, render_reference_markdown

    try:
        return render_reference_markdown(
            parse_reference_document(cleandoc(source)),
            resolve_type_target=anchors.resolve_type_target,
        )
    except ReferenceDocError as error:
        raise ReferenceDocError(f"Failed to render generated reference fragment {source!r}: {error}") from error


def _render_example_block(example: SchemaExample) -> str:
    data = _serialize_example_value(example.value_builder())
    if example.render_format == "yaml":
        rendered = yaml.safe_dump(data, sort_keys=False).rstrip()
    else:
        import json

        rendered = json.dumps(data, indent=2, sort_keys=False)
    return f"```{example.render_format}\n{rendered}\n```"


def _examples_by_root_model(
    exports: tuple[SchemaExport, ...],
) -> dict[type[SitePipelineBaseModel], tuple[SchemaExample, ...]]:
    examples: dict[type[SitePipelineBaseModel], tuple[SchemaExample, ...]] = {}
    for export in exports:
        if not export.examples or len(export.reference_roots) != 1:
            continue
        examples[export.reference_roots[0]] = export.examples
    return examples


def _group_models(
    models: tuple[type[SitePipelineBaseModel], ...],
) -> tuple[tuple[ModelSectionDefinition, tuple[type[SitePipelineBaseModel], ...]], ...]:
    grouped: list[tuple[ModelSectionDefinition, tuple[type[SitePipelineBaseModel], ...]]] = []
    matched_models: set[type[SitePipelineBaseModel]] = set()
    for definition in MODEL_SECTION_DEFINITIONS:
        members = tuple(sorted((model for model in models if definition.matches(model.__module__)), key=lambda model: model.__name__))
        if members:
            grouped.append((definition, members))
            matched_models.update(members)
    unmatched = sorted(model.__name__ for model in models if model not in matched_models)
    if unmatched:
        raise ReferenceDocError(f"Unmatched public reference model modules: {', '.join(unmatched)}")
    return tuple(grouped)


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _serialize_example_value(value: object) -> object:
    """Convert typed example payloads into JSON/YAML-serializable data."""

    if isinstance(value, SitePipelineBaseModel):
        return value.model_dump(by_alias=True, exclude_none=True, mode="json")
    if isinstance(value, tuple):
        return [_serialize_example_value(item) for item in value]
    if isinstance(value, list):
        return [_serialize_example_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported reference example payload type: {type(value)!r}")