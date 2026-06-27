"""
FastAPI dependencies that bind the authenticated user/org onto the mynd request
context and record per-product session activity.

Usage on any product-scoped router:

    @router.post("/...")
    def handler(ctx: MyndContext = Depends(bind_request_context), ...):
        ...

The dependency:
  * reads the product slug (already set on request.state by the middleware)
  * binds user_id / org_id onto the request-scoped ContextVars
  * best-effort records/touches the product_sessions row

It never raises into the request path on bookkeeping failure — Onyx auth has
already validated the user by the time this runs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Depends
from fastapi import Request
from sqlalchemy.orm import Session

from onyx.auth.users import current_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User

from mynd.auth.session import record_product_session
from mynd.context import org_id_ctx
from mynd.context import user_id_ctx
from mynd.routing.product_router import get_product_slug

logger = logging.getLogger("mynd.dependencies")


def _resolve_org_id(user: User) -> str | None:
    """Best-effort org identifier.

    Onyx is multi-tenant; the tenant id is the natural org boundary. Fall back
    to None in single-tenant/self-hosted mode.
    """
    try:
        from onyx.db.engine.sql_engine import (
            get_current_tenant_id,  # type: ignore
        )

        tenant_id = get_current_tenant_id()
        if tenant_id:
            return str(tenant_id)
    except Exception:  # noqa: BLE001
        pass
    return None


@dataclass
class MyndContext:
    product_slug: str | None
    user: User
    org_id: str | None


def bind_request_context(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> MyndContext:
    slug = get_product_slug(request)
    org_id = _resolve_org_id(user)

    user_id_ctx.set(user.id)
    org_id_ctx.set(org_id)

    if slug:
        try:
            record_product_session(
                db,
                user_id=user.id,
                product_slug=slug,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:  # noqa: BLE001 - bookkeeping must not break requests
            logger.exception("failed to record product session")

    return MyndContext(product_slug=slug, user=user, org_id=org_id)
