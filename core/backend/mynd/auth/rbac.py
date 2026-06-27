"""
Per-product RBAC capability resolution.

Onyx EE owns the authoritative RBAC engine (roles, document gating, group
membership). This module sits on top: given Onyx's base role for a user and the
product's ``rbac.yaml``, it resolves the concrete capability set the product UI
should honor. It never *grants* more than Onyx allows — it only narrows/maps.

``rbac.yaml`` shape::

    roles:
      - name: admin
        permissions: [manage_connectors, manage_agents, view_audit_logs]
      - name: member
        permissions: [chat, run_agents, save_conversations]
"""

from __future__ import annotations

from mynd.platform_config.config_loader import get_product_config

# Map Onyx's coarse base roles to the default product role name when a product
# does not explicitly enumerate a matching role.
_ONYX_ROLE_FALLBACK = {
    "admin": "admin",
    "curator": "admin",
    "global_curator": "admin",
    "basic": "member",
    "limited": "member",
}


def resolve_capabilities(product_slug: str, onyx_role: str) -> set[str]:
    """Return the permission strings this user has within ``product_slug``."""
    config = get_product_config(product_slug)
    if config is None:
        return set()

    roles = config.rbac.get("roles", []) or []
    onyx_role_norm = (onyx_role or "basic").lower()

    # 1. Exact match on a product-defined role of the same name.
    for role in roles:
        if str(role.get("name", "")).lower() == onyx_role_norm:
            return set(role.get("permissions", []) or [])

    # 2. Fall back through the Onyx -> product role mapping.
    fallback_name = _ONYX_ROLE_FALLBACK.get(onyx_role_norm, "member")
    for role in roles:
        if str(role.get("name", "")).lower() == fallback_name:
            return set(role.get("permissions", []) or [])

    return set()


def has_capability(product_slug: str, onyx_role: str, capability: str) -> bool:
    return capability in resolve_capabilities(product_slug, onyx_role)
