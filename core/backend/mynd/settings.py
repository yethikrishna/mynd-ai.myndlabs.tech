"""
Runtime flags for the mynd layer.

- MYND_PRODUCT: pins the entire deployment to a single product slug. When set,
  every request is scoped to that product regardless of path/header/cookie. This
  is how a product is deployed as its own standalone app (one image per product,
  one env var, its own domain). Unset = the shared multi-product deployment.

- MYND_RETRIEVAL_ISOLATION: when "true", retrieval is filtered by a
  ``mynd_product`` document tag (plan §8.1). OFF by default because it requires
  documents to be tagged with their product at index time — turning it on
  without index-time tagging would filter out everything. See
  mynd.isolation.retrieval.
"""

from __future__ import annotations

import os


def pinned_product_slug() -> str | None:
    val = os.environ.get("MYND_PRODUCT")
    return val.strip().lower() if val else None


def is_single_product() -> bool:
    return pinned_product_slug() is not None


def retrieval_isolation_enabled() -> bool:
    return os.environ.get("MYND_RETRIEVAL_ISOLATION", "false").lower() in (
        "1",
        "true",
        "yes",
    )
