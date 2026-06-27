"""
Shared cross-product auth wrapper.

This package does NOT replace Onyx's authentication (email/password, SSO/OIDC,
RBAC). Onyx remains the source of identity. We only *augment* it with:

- per-product session tracking  (mynd.auth.session)
- per-product audit logging      (mynd.auth.audit)
- per-product RBAC capability resolution (mynd.auth.rbac)
"""

from mynd.auth.audit import log_product_action
from mynd.auth.rbac import resolve_capabilities
from mynd.auth.session import record_product_session
from mynd.auth.session import touch_product_session

__all__ = [
    "log_product_action",
    "record_product_session",
    "touch_product_session",
    "resolve_capabilities",
]
