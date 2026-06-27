"""
Product context routing.

Every request to ``ai.myndlabs.tech/<slug>/...`` carries a product slug as the
first path segment. This middleware extracts it and stashes it on
``request.state.product_slug`` so downstream handlers, the audit logger and the
LLM credential resolver can all read a single source of truth.

The set of valid slugs is discovered from the ``config/`` directory at startup
(see ``mynd.platform_config``), so adding a product is a config-only change.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from mynd.platform_config.config_loader import list_product_slugs

# Path prefixes that are global (not product-scoped) and must never be treated
# as a product slug.
RESERVED_PREFIXES: set[str] = {
    "api",
    "auth",
    "oauth",
    "health",
    "static",
    "_next",
    "assets",
    "admin",
}

# Resolved once at import; refreshed by ProductContextMiddleware on first use so
# tests and hot-reload pick up new config dirs.
KNOWN_PRODUCT_SLUGS: set[str] = set(list_product_slugs())


def extract_slug_from_path(path: str, known: set[str]) -> str | None:
    """Return the product slug for a path, or ``None`` if not product-scoped."""
    segments = [s for s in path.split("/") if s]
    if not segments:
        return None
    first = segments[0].lower()
    if first in RESERVED_PREFIXES:
        return None
    if first in known:
        return first
    return None


def get_product_slug(request: Request) -> str | None:
    """Dependency/helper to read the resolved slug off request state."""
    return getattr(request.state, "product_slug", None)


class ProductContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, refresh_slugs: bool = True) -> None:
        super().__init__(app)
        self._refresh_slugs = refresh_slugs

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        known = KNOWN_PRODUCT_SLUGS
        if self._refresh_slugs and not known:
            known = set(list_product_slugs())
            KNOWN_PRODUCT_SLUGS.update(known)

        slug = extract_slug_from_path(request.url.path, known)
        request.state.product_slug = slug

        # Mirror onto the request-scoped ContextVar so deep Onyx call paths
        # (e.g. the LLM factory) can read it without signature changes.
        from mynd.context import product_slug_ctx

        token = product_slug_ctx.set(slug)
        try:
            return await call_next(request)
        finally:
            product_slug_ctx.reset(token)
