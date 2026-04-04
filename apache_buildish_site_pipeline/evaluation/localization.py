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

"""Localization-aware validations over resolved content plans."""

from __future__ import annotations

from collections import defaultdict

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, RouteMode
from apache_buildish_site_pipeline.planning.types import PlanningEvaluation, ResolvedComponentConfig

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import PageScanResult, ScannedPage


def validate_localization(
    *,
    planning: PlanningEvaluation,
    page_scan: PageScanResult,
    collector: DiagnosticCollector,
) -> None:
    """Validate resolved localization policy and translatable-page grouping."""

    components_by_slug = {component.slug: component for component in planning.site.components}
    for component in planning.site.components:
        _validate_policy(component=component, collector=collector)

    pages_by_translation: dict[tuple[str, str, str], dict[str, ScannedPage]] = defaultdict(dict)
    translation_key_by_sibling_path: dict[tuple[str, str, str], str] = {}
    for page in page_scan.pages:
        if page.translation_key is None or page.component_slug is None or page.artifact_key is None:
            continue
        component = components_by_slug[page.component_slug]
        locales = component.localization.supported_locales
        if component.localization.route_mode is not RouteMode.PREFIX_ALL or not locales:
            continue
        locale = _locale_prefix(page.relative_path, locales)
        if locale is None:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.TRANSLATION_LOCALE_UNRESOLVED,
                message=(
                    f"Translated page {page.relative_path} for {page.component_slug}/{page.artifact_key} "
                    "does not live beneath a supported locale prefix"
                ),
                component_slug=page.component_slug,
                artifact_key=page.artifact_key,
                details={
                    "inputId": page.input_id,
                    "path": page.relative_path,
                    "translationKey": page.translation_key,
                    "supportedLocales": list(locales),
                },
            )
            continue
        sibling_suffix = page.relative_path.partition("/")[2]
        sibling_key = (page.component_slug, page.artifact_key, sibling_suffix)
        existing_translation_key = translation_key_by_sibling_path.get(sibling_key)
        if existing_translation_key is not None and existing_translation_key != page.translation_key:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.TRANSLATION_LINKAGE_CONFLICT,
                message=(
                    f"Translated sibling route {sibling_suffix} for {page.component_slug}/{page.artifact_key} "
                    "is linked to multiple translation keys"
                ),
                component_slug=page.component_slug,
                artifact_key=page.artifact_key,
                details={
                    "path": sibling_suffix,
                    "translationKeys": [existing_translation_key, page.translation_key],
                },
            )
            continue
        translation_key_by_sibling_path[sibling_key] = page.translation_key
        translation_group = pages_by_translation[(page.component_slug, page.artifact_key, page.translation_key)]
        existing = translation_group.get(locale)
        if existing is not None:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.TRANSLATION_LOCALE_DUPLICATE,
                message=(
                    f"Translation set {page.translation_key} for {page.component_slug}/{page.artifact_key} "
                    f"contains more than one page for locale {locale}"
                ),
                component_slug=page.component_slug,
                artifact_key=page.artifact_key,
                details={
                    "translationKey": page.translation_key,
                    "locale": locale,
                    "paths": [existing.relative_path, page.relative_path],
                },
            )
            continue
        translation_group[locale] = page

    for (component_slug, artifact_key, translation_key), localized_pages in pages_by_translation.items():
        sibling_suffixes = {page.relative_path.partition("/")[2] for page in localized_pages.values()}
        if len(sibling_suffixes) <= 1:
            continue
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.TRANSLATION_ROUTE_INCONSISTENT,
            message=(
                f"Translation set {translation_key} for {component_slug}/{artifact_key} does not resolve "
                "to a consistent sibling route across locales"
            ),
            component_slug=component_slug,
            artifact_key=artifact_key,
            details={
                "translationKey": translation_key,
                "routesByLocale": {
                    locale: page.relative_path.partition("/")[2]
                    for locale, page in sorted(localized_pages.items())
                },
            },
        )


def _validate_policy(*, component: ResolvedComponentConfig, collector: DiagnosticCollector) -> None:
    localization = component.localization
    locales = localization.supported_locales
    if localization.route_mode is RouteMode.PREFIX_ALL and not locales:
        _add_policy_error(component=component, collector=collector, message="Locale-prefixed routing requires supportedLocales")
    if localization.route_mode is RouteMode.PREFIX_ALL and localization.default_locale is None:
        _add_policy_error(component=component, collector=collector, message="Locale-prefixed routing requires defaultLocale")
    if localization.default_locale is not None and locales is not None and localization.default_locale not in locales:
        _add_policy_error(component=component, collector=collector, message="defaultLocale must be included in supportedLocales")
    if localization.fallback_locale is not None and locales is not None and localization.fallback_locale not in locales:
        _add_policy_error(component=component, collector=collector, message="fallbackLocale must be included in supportedLocales")


def _add_policy_error(*, component: ResolvedComponentConfig, collector: DiagnosticCollector, message: str) -> None:
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.LOCALIZATION_POLICY_INVALID,
        message=f"Localization policy for component {component.slug} is invalid: {message}",
        component_slug=component.slug,
        details={
            "defaultLocale": component.localization.default_locale,
            "supportedLocales": list(component.localization.supported_locales or ()),
            "fallbackLocale": component.localization.fallback_locale,
            "routeMode": component.localization.route_mode.value if component.localization.route_mode else None,
        },
    )


def _locale_prefix(relative_path: str, supported_locales: tuple[str, ...]) -> str | None:
    first_segment = relative_path.split("/", 1)[0]
    return first_segment if first_segment in supported_locales else None
