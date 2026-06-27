"""
Public product-config endpoint consumed by the frontend at boot.

    GET /api/config            -> list of available product slugs
    GET /api/config/{slug}     -> public branding/feature config for a product

Only the browser-safe subset (``ProductConfig.public_dict``) is returned;
RBAC/connector internals stay server-side.
"""

from __future__ import annotations

from fastapi import APIRouter

from onyx.error_handling.error_codes import OnyxErrorCode
from onyx.error_handling.exceptions import OnyxError

from mynd.platform_config.config_loader import get_product_config
from mynd.platform_config.config_loader import list_product_slugs

router = APIRouter(prefix="/api/config", tags=["mynd-config"])


@router.get("")
def list_products() -> dict:
    return {"products": list_product_slugs()}


@router.get("/{slug}")
def get_product(slug: str) -> dict:
    config = get_product_config(slug)
    if config is None:
        raise OnyxError(OnyxErrorCode.NOT_FOUND, f"Unknown product '{slug}'.")
    return config.public_dict()
