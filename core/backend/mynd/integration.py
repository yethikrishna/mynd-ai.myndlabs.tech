"""
Single entry point that wires the mynd layer into the Onyx FastAPI app.

Onyx's ``onyx/main.py::get_application`` builds the app. To attach mynd without
editing Onyx's router list inline, add ONE call near the end of
``get_application`` (just before ``return application``)::

    from mynd.integration import register_mynd
    register_mynd(application)

That single line:
  * installs the product-context middleware (request.state.product_slug)
  * mounts the config, llm-credential, and oauth-callback routers
  * is idempotent and safe to call once per app instance

Keeping the wiring in one function (rather than scattered edits) minimizes the
diff against upstream Onyx and makes rebases against new Onyx releases trivial.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

logger = logging.getLogger("mynd.integration")

_REGISTERED_FLAG = "_mynd_registered"


def register_mynd(application: FastAPI) -> None:
    if getattr(application.state, _REGISTERED_FLAG, False):
        return

    from mynd.llm_auth.router import oauth_callback_router
    from mynd.llm_auth.router import router as llm_credentials_router
    from mynd.routing.product_router import ProductContextMiddleware
    from mynd.server.config_router import router as config_router

    # Middleware runs for every request: stamps request.state.product_slug.
    application.add_middleware(ProductContextMiddleware)

    # Routers. Onyx prepends its own global API prefix to included routers via
    # include_router_with_global_prefix_prepended, but these paths are already
    # absolute (/api/..., /oauth/...) and are intentionally registered raw.
    application.include_router(config_router)
    application.include_router(llm_credentials_router)
    application.include_router(oauth_callback_router)

    setattr(application.state, _REGISTERED_FLAG, True)
    logger.info("mynd layer registered on Onyx FastAPI app")
