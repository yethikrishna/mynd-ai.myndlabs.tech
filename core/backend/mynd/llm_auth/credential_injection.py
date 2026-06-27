"""
Inference-time credential injection.

Onyx's ``onyx.llm.factory.llm_from_provider`` builds an ``LLM`` from a system
``LLMProviderView``. This adapter lets a user/org BYO credential transparently
override the system one for the duration of a request, using the request-scoped
``mynd.context`` ContextVars (so no Onyx signatures change).

Integration is a single guarded call in ``llm_from_provider``:

    from mynd.llm_auth.credential_injection import maybe_override_provider
    llm_provider = maybe_override_provider(llm_provider)

``maybe_override_provider`` returns the provider unchanged when there is no
applicable user/org credential (the common case / system scope), so Onyx's
default behavior is preserved.
"""

from __future__ import annotations

import copy
import logging

from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.server.manage.llm.models import LLMProviderView

from mynd.context import llm_credential_scope_ctx
from mynd.context import org_id_ctx
from mynd.context import product_slug_ctx
from mynd.context import user_id_ctx
from mynd.db.models import CredentialScope
from mynd.llm_auth.resolver import resolve_llm_credential

logger = logging.getLogger("mynd.credential_injection")


def maybe_override_provider(llm_provider: LLMProviderView) -> LLMProviderView:
    """Return a copy of ``llm_provider`` with user/org creds applied, or the
    original if none apply. Records the resolved scope on the request context.
    """
    product_slug = product_slug_ctx.get()
    user_id = user_id_ctx.get()
    org_id = org_id_ctx.get()

    # Nothing to do outside a product-scoped request (e.g. background jobs).
    if not product_slug:
        llm_credential_scope_ctx.set(CredentialScope.SYSTEM)
        return llm_provider

    try:
        with get_session_with_current_tenant() as db:
            resolved = resolve_llm_credential(
                db,
                provider_name=llm_provider.provider,
                product_slug=product_slug,
                user_id=user_id,
                org_id=org_id,
            )
    except Exception:  # noqa: BLE001 - never break inference on resolver errors
        logger.exception("mynd credential resolution failed; using system creds")
        llm_credential_scope_ctx.set(CredentialScope.SYSTEM)
        return llm_provider

    llm_credential_scope_ctx.set(resolved.scope)

    if resolved.scope == CredentialScope.SYSTEM:
        return llm_provider

    # Apply the user/org secret material onto a copy of the provider view.
    overridden = copy.copy(llm_provider)
    payload = resolved.payload or {}
    if payload.get("api_key"):
        overridden.api_key = payload["api_key"]
    if resolved.base_url:
        overridden.api_base = resolved.base_url

    # OAuth bearer tokens are surfaced as the api_key for OpenAI-style providers;
    # provider-specific handling (e.g. GCP service-account JSON) can extend here.
    if payload.get("access_token") and not payload.get("api_key"):
        overridden.api_key = payload["access_token"]

    return overridden
