"""
Per-product session tracking that wraps (never replaces) Onyx auth.

Flow:
1. User authenticates via Onyx CE/EE (Onyx issues its own token/cookie).
2. On first product request we ``record_product_session`` for (user, slug).
3. Every subsequent request ``touch_product_session`` updates last_active.

None of this gates access — Onyx's own session validation still runs first.
These helpers are best-effort and must never raise into the request path.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from mynd.db.models import ProductSession


def record_product_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    product_slug: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ProductSession:
    """Create (or reuse) a session row for this user+product."""
    existing = db.execute(
        select(ProductSession)
        .where(ProductSession.user_id == user_id)
        .where(ProductSession.product_slug == product_slug)
        .order_by(ProductSession.last_active.desc())
        .limit(1)
    ).scalar_one_or_none()

    if existing is not None:
        existing.ip_address = ip_address or existing.ip_address
        existing.user_agent = user_agent or existing.user_agent
        db.add(existing)
        db.commit()
        return existing

    session = ProductSession(
        user_id=user_id,
        product_slug=product_slug,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    return session


def touch_product_session(
    db: Session, *, user_id: uuid.UUID, product_slug: str
) -> None:
    """Bump last_active for the most recent session of this user+product."""
    from sqlalchemy import func
    from sqlalchemy import update

    db.execute(
        update(ProductSession)
        .where(ProductSession.user_id == user_id)
        .where(ProductSession.product_slug == product_slug)
        .values(last_active=func.now())
    )
    db.commit()
