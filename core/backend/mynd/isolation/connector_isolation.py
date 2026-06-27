"""
Connector isolation (plan §8.2).

A product may only use the connectors enumerated in its config, with the scopes
and data filters declared there. Connector credentials are segmented per
product/org so one team's connectors are never reused by another product.

    allowed_connectors("grc")          -> {"confluence", "google_drive", ...}
    is_connector_allowed("grc", "github") -> False
    connector_scopes("grc", "confluence") -> {"scopes": ["pages_read"], "filters": {...}}
"""

from __future__ import annotations

from mynd.platform_config.config_loader import get_product_config


def allowed_connectors(product_slug: str) -> set[str]:
    config = get_product_config(product_slug)
    if config is None:
        return set()
    # `enabled_connectors` (product.yaml) is authoritative; connectors.yaml
    # refines scopes for those that are enabled.
    return set(config.enabled_connectors)


def is_connector_allowed(product_slug: str, connector: str) -> bool:
    return connector in allowed_connectors(product_slug)


def connector_scopes(product_slug: str, connector: str) -> dict:
    """Return ``{"scopes": [...], "filters": {...}}`` for a connector, or {}."""
    config = get_product_config(product_slug)
    if config is None:
        return {}
    spec = (config.connectors.get("connectors", {}) or {}).get(connector)
    if not spec:
        return {}
    return {
        "scopes": spec.get("scopes", []) or [],
        "filters": spec.get("filters", {}) or {},
    }


def assert_connector_allowed(product_slug: str, connector: str) -> None:
    """Raise OnyxError if a product is not permitted to use ``connector``."""
    if is_connector_allowed(product_slug, connector):
        return
    from onyx.error_handling.error_codes import OnyxErrorCode
    from onyx.error_handling.exceptions import OnyxError

    raise OnyxError(
        OnyxErrorCode.INSUFFICIENT_PERMISSIONS,
        f"Connector '{connector}' is not enabled for product '{product_slug}'.",
    )
