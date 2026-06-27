"""
Authenticated product endpoints (capabilities for the current user).

    GET /api/product/{slug}/capabilities

Returns the resolved capability set for the signed-in user within the product,
derived from their Onyx base role + ``config/<slug>/rbac.yaml``. The frontend
uses this to gate UI (e.g. show connector/model-settings admin actions).
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from onyx.auth.users import current_user
from onyx.db.models import User

from mynd.auth.rbac import resolve_capabilities

router = APIRouter(prefix="/api/product", tags=["mynd-product"])


@router.get("/{slug}/capabilities")
def get_capabilities(
    slug: str,
    user: User = Depends(current_user),
) -> dict:
    onyx_role = getattr(user.role, "value", str(user.role))
    caps = resolve_capabilities(slug, onyx_role)
    return {
        "slug": slug,
        "role": onyx_role,
        "capabilities": sorted(caps),
    }
