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
from sqlalchemy.orm import Session

from onyx.auth.users import current_curator_or_admin_user
from onyx.auth.users import current_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User

from mynd.auth.rbac import resolve_capabilities
from mynd.db.connector_map import get_product_for_cc_pair
from mynd.db.connector_map import list_cc_pairs_for_product
from mynd.db.connector_map import set_product_for_cc_pair
from mynd.db.connector_map import unset_product_for_cc_pair

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


# --------------------------------------------------------------------------- #
# Connector → product binding (admin) — enables retrieval isolation by tagging
# the connector's documents with the product at index time.
# --------------------------------------------------------------------------- #
@router.get("/{slug}/connectors")
def list_product_connectors(
    slug: str,
    _admin: User = Depends(current_curator_or_admin_user),
    db: Session = Depends(get_session),
) -> dict:
    return {"slug": slug, "cc_pair_ids": list_cc_pairs_for_product(db, slug)}


@router.put("/{slug}/connectors/{cc_pair_id}", status_code=204)
def bind_connector(
    slug: str,
    cc_pair_id: int,
    _admin: User = Depends(current_curator_or_admin_user),
    db: Session = Depends(get_session),
) -> None:
    set_product_for_cc_pair(db, cc_pair_id, slug)


@router.delete("/{slug}/connectors/{cc_pair_id}", status_code=204)
def unbind_connector(
    slug: str,
    cc_pair_id: int,
    _admin: User = Depends(current_curator_or_admin_user),
    db: Session = Depends(get_session),
) -> None:
    # Only unbind if it actually belongs to this product.
    if get_product_for_cc_pair(db, cc_pair_id) == slug:
        unset_product_for_cc_pair(db, cc_pair_id)
