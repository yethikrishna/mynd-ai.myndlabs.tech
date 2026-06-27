"""
Request-scoped context for the mynd layer.

FastAPI runs dependencies and the endpoint in the same task, and Onyx's
synchronous DB/LLM calls run inline within that task, so ``ContextVar``s set in a
dependency/middleware are visible to the entire downstream call stack (including
``onyx.llm.factory``). We use that to thread product/user/org through Onyx's deep
call chain **without changing any Onyx function signatures**.

Set by:
- ``ProductContextMiddleware`` (product slug, from the URL)
- ``mynd.dependencies.bind_request_context`` (user/org, after Onyx auth)

Read by:
- ``mynd.llm_auth.credential_injection`` (which credential to use)
- ``mynd.auth.audit`` (which scope served a request)
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

product_slug_ctx: ContextVar[str | None] = ContextVar("mynd_product_slug", default=None)
user_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("mynd_user_id", default=None)
org_id_ctx: ContextVar[str | None] = ContextVar("mynd_org_id", default=None)

# Set by credential_injection so the audit logger can record which scope
# (user/org/system) actually served the most recent LLM call on this request.
llm_credential_scope_ctx: ContextVar[str | None] = ContextVar(
    "mynd_llm_credential_scope", default=None
)


def current_product_slug() -> str | None:
    return product_slug_ctx.get()


def current_user_id() -> uuid.UUID | None:
    return user_id_ctx.get()


def current_org_id() -> str | None:
    return org_id_ctx.get()


def current_llm_credential_scope() -> str | None:
    return llm_credential_scope_ctx.get()
