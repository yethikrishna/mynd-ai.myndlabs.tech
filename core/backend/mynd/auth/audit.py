"""
Per-product audit logging.

A single ``log_product_action`` entry point is called from significant code
paths (chat send, RAG query, connector fetch, agent run, admin change). It
writes to ``mynd_shared.product_audit_logs`` and is intentionally tolerant:
auditing must never break the user-facing request.

Example
-------
    log_product_action(
        db,
        user_id=user.id,
        org_id=org_id,
        product_slug=request.state.product_slug,
        action="chat.send",
        resource_type="conversation",
        resource_id=str(conversation_id),
        llm_provider="openai",
        llm_credential_scope=CredentialScope.USER,
    )
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from mynd.db.models import ProductAuditLog

logger = logging.getLogger("mynd.audit")


def log_product_action(
    db: Session,
    *,
    product_slug: str | None,
    action: str,
    user_id: uuid.UUID | None = None,
    org_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    llm_provider: str | None = None,
    llm_credential_scope: str | None = None,
) -> None:
    try:
        entry = ProductAuditLog(
            user_id=user_id,
            org_id=org_id,
            product_slug=product_slug or "unknown",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            llm_provider=llm_provider,
            llm_credential_scope=llm_credential_scope,
        )
        db.add(entry)
        db.commit()
    except Exception:  # noqa: BLE001 - auditing must never break the request
        db.rollback()
        logger.exception(
            "Failed to write product audit log (action=%s slug=%s)",
            action,
            product_slug,
        )
