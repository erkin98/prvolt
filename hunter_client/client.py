from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional, TypedDict, cast

import requests


class HunterError(Exception):
    """Represents an error response from the Hunter.io API."""


class DiscoverParams(TypedDict, total=False):
    query: str
    domain: str
    company: str
    industry: str
    country: str
    city: str
    size_from: int
    size_to: int
    type: str
    limit: int
    offset: int


class DomainSearchParams(TypedDict, total=False):
    domain: str
    company: str
    limit: int
    offset: int
    type: str


class EmailFinderParams(TypedDict):
    domain: str
    first_name: str
    last_name: str


KEY_QUERY = "query"
KEY_DOMAIN = "domain"
KEY_COMPANY = "company"
KEY_INDUSTRY = "industry"
KEY_COUNTRY = "country"
KEY_CITY = "city"
KEY_SIZE_FROM = "size_from"
KEY_SIZE_TO = "size_to"
KEY_TYPE = "type"
KEY_LIMIT = "limit"
KEY_OFFSET = "offset"
KEY_FIRST_NAME = "first_name"
KEY_LAST_NAME = "last_name"

DISCOVER_ALLOWED_KEYS = (
    KEY_QUERY,
    KEY_DOMAIN,
    KEY_COMPANY,
    KEY_INDUSTRY,
    KEY_COUNTRY,
    KEY_CITY,
    KEY_SIZE_FROM,
    KEY_SIZE_TO,
    KEY_TYPE,
    KEY_LIMIT,
    KEY_OFFSET,
)

DOMAIN_SEARCH_ALLOWED_KEYS = (
    KEY_COMPANY,
    KEY_LIMIT,
    KEY_OFFSET,
    KEY_TYPE,
)


def _perform_get(
    base_url: str,
    endpoint: str,
    api_key: str,
    timeout_seconds: int,
    params: Mapping[str, Any],
) -> Dict[str, Any]:
    url = "/".join((base_url.rstrip("/"), endpoint.lstrip("/")))
    query_params: MutableMapping[str, Any] = {"api_key": api_key}
    query_params.update(params)
    response = requests.get(url, params=query_params, timeout=timeout_seconds)
    if response.status_code >= 400:
        message = _extract_error_message(response)
        raise HunterError(f"{response.status_code}: {message}")
    try:
        parsed: Dict[str, Any] = response.json()
    except ValueError as exc:
        raise HunterError("Invalid JSON response") from exc
    return parsed


def _extract_error_message(response: requests.Response) -> str:
    try:
        payload: Dict[str, Any] = response.json()
    except ValueError:
        payload = {}
    return payload.get("errors") or payload.get("message") or response.text


@dataclass(frozen=True)
class HunterClient:
    api_key: str
    base_url: str = "https://api.hunter.io/v2"
    timeout_seconds: int = 15

    # Endpoint 1: Discover companies
    def discover(self, **params: Any) -> Dict[str, Any]:
        values: Dict[str, Any] = {
            key: params[key] for key in DISCOVER_ALLOWED_KEYS if key in params
        }
        typed: DiscoverParams = cast(DiscoverParams, values)
        return _perform_get(
            self.base_url,
            "discover",
            self.api_key,
            self.timeout_seconds,
            typed,
        )

    # Endpoint 2: Domain search
    def domain_search(
        self,
        *,
        domain: Optional[str] = None,
        **params: Any,
    ) -> Dict[str, Any]:
        values: Dict[str, Any] = {
            key: params[key] for key in DOMAIN_SEARCH_ALLOWED_KEYS if key in params
        }
        if domain is not None:
            values[KEY_DOMAIN] = domain
        typed: DomainSearchParams = cast(DomainSearchParams, values)
        return _perform_get(
            self.base_url,
            "domain-search",
            self.api_key,
            self.timeout_seconds,
            typed,
        )

    # Endpoint 3: Email finder
    def email_finder(
        self,
        *,
        domain: str,
        first_name: str,
        last_name: str,
    ) -> Dict[str, Any]:
        typed: EmailFinderParams = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
        }
        return _perform_get(
            self.base_url,
            "email-finder",
            self.api_key,
            self.timeout_seconds,
            typed,
        )

    # Human-friendly convenience API
    def search_companies(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Discover companies by a simple text query."""
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if offset < 0:
            raise ValueError("offset must be a non-negative integer")
        return _perform_get(
            self.base_url,
            "discover",
            self.api_key,
            self.timeout_seconds,
            {KEY_QUERY: query, KEY_LIMIT: limit, KEY_OFFSET: offset},
        )

    def emails_for_domain(
        self,
        domain: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Fetch emails discovered for a domain with basic pagination."""
        if not domain or not domain.strip():
            raise ValueError("domain must be a non-empty string")
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if offset < 0:
            raise ValueError("offset must be a non-negative integer")
        return _perform_get(
            self.base_url,
            "domain-search",
            self.api_key,
            self.timeout_seconds,
            {KEY_DOMAIN: domain, KEY_LIMIT: limit, KEY_OFFSET: offset},
        )

    def guess_email(
        self,
        domain: str,
        first_name: str,
        last_name: str,
    ) -> Dict[str, Any]:
        """Find the most likely email address for a person at a domain."""
        if not domain or not domain.strip():
            raise ValueError("domain must be a non-empty string")
        if not first_name or not first_name.strip():
            raise ValueError("first_name must be a non-empty string")
        if not last_name or not last_name.strip():
            raise ValueError("last_name must be a non-empty string")
        return self.email_finder(
            domain=domain,
            first_name=first_name,
            last_name=last_name,
        )

    def _get(self, endpoint: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        # Internal method retained for compatibility.
        return _perform_get(
            self.base_url,
            endpoint,
            self.api_key,
            self.timeout_seconds,
            params,
        )
