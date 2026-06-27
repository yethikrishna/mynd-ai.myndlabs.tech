"""
Thin, best-effort audit hooks to call from Onyx code paths.

Each hook opens its own short-lived session and swallows all errors so auditing
can never break the user-facing request. Keep the Onyx-side edit to a single
import + call.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("mynd.audit_hooks")


def audit_chat_send(request, user) -> None:
    """Record a ``chat.send`` action for the current product, if any.

    Product context comes from the request (header/cookie/path) via the
    middleware-populated ``request.state.product_slug``; the resolved LLM
    credential scope is read from the request ContextVar by the logger.
    """
    try:
        slug = getattr(request.state, "product_slug", None)
        if not slug:
            return  # not a product-scoped request; nothing to record
        from onyx.db.engine.sql_engine import get_session_with_current_tenant

        from mynd.auth.audit import log_product_action

        user_id = getattr(user, "id", None)
        with get_session_with_current_tenant() as db:
            log_product_action(
                db,
                action="chat.send",
                product_slug=slug,
                user_id=user_id,
                resource_type="conversation",
            )
    except Exception:  # noqa: BLE001 - auditing must never break chat
        logger.exception("audit_chat_send failed")
