"""
Index namespacing for per-product / per-org RAG isolation (plan §8.1).

RAG indices and retrieval queries are namespaced by ``product_slug`` + ``org_id``
so that, e.g., ``eng`` documents for org 42 never surface in a ``grc`` query.

    index_namespace("eng", "org42", "github")  -> "eng__org42__github"
    retrieval_filter("eng", "org42")            -> {"product_slug": "eng",
                                                    "org_id": "org42"}

The retrieval filter is meant to be ANDed into the vector-store metadata filter
(Onyx attaches it alongside its own ACL filters), and combined with the user's
RBAC permissions — never used as the sole gate.
"""

from __future__ import annotations

import re

_SAFE = re.compile(r"[^a-zA-Z0-9]+")
_SEP = "__"


def _slugify(value: str) -> str:
    return _SAFE.sub("-", value.strip().lower()).strip("-")


def index_namespace(product_slug: str, org_id: str | None, source: str | None = None) -> str:
    """Build a stable index namespace string for a product/org/(source)."""
    parts = [_slugify(product_slug), _slugify(org_id or "shared")]
    if source:
        parts.append(_slugify(source))
    return _SEP.join(parts)


def retrieval_filter(product_slug: str, org_id: str | None) -> dict[str, str]:
    """Metadata filter to AND into every retrieval for this product/org."""
    flt = {"product_slug": _slugify(product_slug)}
    if org_id:
        flt["org_id"] = _slugify(org_id)
    return flt
