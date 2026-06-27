"""
DB helpers for the connector→product binding (mynd_shared.connector_product_map).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from mynd.db.models import ConnectorProductMap


def get_product_for_cc_pair(db: Session, cc_pair_id: int) -> str | None:
    return db.execute(
        select(ConnectorProductMap.product_slug).where(
            ConnectorProductMap.cc_pair_id == cc_pair_id
        )
    ).scalar_one_or_none()


def set_product_for_cc_pair(db: Session, cc_pair_id: int, product_slug: str) -> None:
    existing = db.get(ConnectorProductMap, cc_pair_id)
    if existing is None:
        db.add(ConnectorProductMap(cc_pair_id=cc_pair_id, product_slug=product_slug))
    else:
        existing.product_slug = product_slug
        db.add(existing)
    db.commit()


def unset_product_for_cc_pair(db: Session, cc_pair_id: int) -> None:
    existing = db.get(ConnectorProductMap, cc_pair_id)
    if existing is not None:
        db.delete(existing)
        db.commit()


def list_cc_pairs_for_product(db: Session, product_slug: str) -> list[int]:
    return list(
        db.execute(
            select(ConnectorProductMap.cc_pair_id).where(
                ConnectorProductMap.product_slug == product_slug
            )
        )
        .scalars()
        .all()
    )
