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

"""Validation helpers for URL-bearing wire fields."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from .common import _validate_no_structural_whitespace_or_controls

_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})
_NON_PUBLIC_HOST_SUFFIXES = (".internal", ".local", ".localhost")


def validate_url_string(value: str) -> str:
    """Validate an absolute public-contract URL string."""
    value = _validate_no_structural_whitespace_or_controls(value, type_name="UrlString")
    parsed_url = urlsplit(value)

    if parsed_url.scheme not in _ALLOWED_URL_SCHEMES:
        raise ValueError("UrlString must use an allowed absolute URL scheme")
    if not parsed_url.netloc:
        raise ValueError("UrlString must be absolute and include a host")
    if parsed_url.username is not None or parsed_url.password is not None:
        raise ValueError("UrlString must not embed userinfo credentials")
    return value


def validate_provider_base_url(value: str) -> str:
    """Validate a public human-facing provider home URL."""
    value = validate_url_string(value)
    parsed_url = urlsplit(value)
    hostname = parsed_url.hostname
    if hostname is None:
        raise ValueError("Provider baseUrl must include a hostname")

    lowered_hostname = hostname.lower()
    if lowered_hostname == "localhost" or lowered_hostname.endswith(_NON_PUBLIC_HOST_SUFFIXES):
        raise ValueError("Provider baseUrl must not use a non-public hostname")

    try:
        parsed_ip = ipaddress.ip_address(lowered_hostname)
    except ValueError:
        parsed_ip = None

    if parsed_ip is not None and (
        parsed_ip.is_private
        or parsed_ip.is_loopback
        or parsed_ip.is_link_local
        or parsed_ip.is_reserved
        or parsed_ip.is_multicast
        or parsed_ip.is_unspecified
    ):
        raise ValueError("Provider baseUrl must not use a non-public IP address")

    first_label = lowered_hostname.split(".", maxsplit=1)[0]
    if first_label == "api":
        raise ValueError("Provider baseUrl must be human-facing rather than a raw API endpoint")
    if parsed_url.query or parsed_url.fragment:
        raise ValueError("Provider baseUrl must not carry query or fragment components")
    return value