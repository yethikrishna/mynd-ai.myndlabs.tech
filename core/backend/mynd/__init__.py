"""
mynd Core — the Mynd Labs layer that wraps and extends the forked Onyx platform.

This package lives *inside* the Onyx backend (``core/backend``) so it can import
Onyx primitives (``onyx.db``, ``onyx.auth``, ``onyx.llm`` …) directly and mount
itself into the existing FastAPI application without modifying Onyx's own auth
or RBAC logic.

Conceptual mapping to the architecture plan (see /ARCHITECTURE.md):

    plan: core/auth/            -> mynd.auth        (session + audit wrappers)
    plan: core/llm_auth/        -> mynd.llm_auth    (user/org keys, OAuth, resolver)
    plan: core/platform_config/ -> mynd.platform_config (global config loading)
    plan: core/backend/routing/ -> mynd.routing     (product-slug routing)

All persistent state introduced by this layer lives in the dedicated
``mynd_shared`` Postgres schema so it never collides with Onyx's CE/EE tables.
"""

MYND_SHARED_SCHEMA = "mynd_shared"

__all__ = ["MYND_SHARED_SCHEMA"]
