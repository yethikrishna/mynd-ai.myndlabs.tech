"""
Query-time retrieval isolation (plan §8.1), reusing Onyx's existing document
``tags`` metadata filter (no Vespa schema change).

When ``MYND_RETRIEVAL_ISOLATION`` is enabled and the request is product-scoped,
``apply_retrieval_isolation`` ANDs a ``mynd_product`` (and ``mynd_org``) tag into
the search filters, so retrieval only returns documents tagged with this
product/org — in addition to Onyx's own ACL filtering, never instead of it.

Two-sided requirement: documents must be tagged with these same tags at index
time (``product_document_tags``), otherwise the filter matches nothing. That is
why the flag is OFF by default — enable it only once your connectors tag their
documents with the product (the connector→product binding). See
``mynd.isolation.connector_isolation`` for the per-product connector config.
"""

from __future__ import annotations

from mynd.context import current_org_id
from mynd.context import current_product_slug
from mynd.settings import retrieval_isolation_enabled

TAG_PRODUCT = "mynd_product"
TAG_ORG = "mynd_org"


def product_document_tags(product_slug: str, org_id: str | None) -> dict[str, str]:
    """Tags to attach to a document's metadata at index time."""
    tags = {TAG_PRODUCT: product_slug}
    if org_id:
        tags[TAG_ORG] = org_id
    return tags


def apply_retrieval_isolation(filters):
    """Return ``filters`` with the product/org tag ANDed in, when applicable.

    Typed loosely to avoid importing Onyx search models at module import time;
    ``filters`` is an ``onyx.context.search.models.IndexFilters``.
    """
    if not retrieval_isolation_enabled():
        return filters

    slug = current_product_slug()
    if not slug:
        return filters

    from onyx.context.search.models import Tag

    extra = [Tag(tag_key=TAG_PRODUCT, tag_value=slug)]
    org_id = current_org_id()
    if org_id:
        extra.append(Tag(tag_key=TAG_ORG, tag_value=org_id))

    existing = list(filters.tags or [])
    filters.tags = existing + extra
    return filters
