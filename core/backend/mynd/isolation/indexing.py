"""
Index-time document tagging for retrieval isolation (plan §8.1).

When a connector is bound to a product (``mynd_shared.connector_product_map``),
every document it indexes gets a ``mynd_product`` (and ``mynd_org``) tag injected
into its metadata. Those tags are what ``mynd.isolation.retrieval`` filters on at
query time. This is the index-time half that makes ``MYND_RETRIEVAL_ISOLATION``
safe to enable.

The hook is best-effort and a no-op when:
  * the connector has no product binding, or
  * isolation is globally disabled.
It mutates each document's ``metadata`` dict in place.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from mynd.context import current_org_id
from mynd.db.connector_map import get_product_for_cc_pair
from mynd.isolation.retrieval import TAG_ORG
from mynd.isolation.retrieval import TAG_PRODUCT
from mynd.settings import retrieval_isolation_enabled

logger = logging.getLogger("mynd.indexing_isolation")


def tag_documents_for_index(documents, index_attempt_metadata, db_session: Session) -> None:
    """Inject product/org tags into each document's metadata, if bound.

    ``documents`` is a list of ``onyx.connectors.models.Document``;
    ``index_attempt_metadata`` carries ``connector_id`` + ``credential_id``.
    """
    if not retrieval_isolation_enabled():
        return
    try:
        from onyx.db.connector_credential_pair import get_connector_credential_pair

        cc_pair = get_connector_credential_pair(
            db_session,
            index_attempt_metadata.connector_id,
            index_attempt_metadata.credential_id,
        )
        if cc_pair is None:
            return
        product_slug = get_product_for_cc_pair(db_session, cc_pair.id)
        if not product_slug:
            return

        org_id = current_org_id()
        for doc in documents:
            meta = getattr(doc, "metadata", None)
            if meta is None:
                continue
            meta[TAG_PRODUCT] = product_slug
            if org_id:
                meta[TAG_ORG] = org_id
    except Exception:  # noqa: BLE001 - tagging must never break indexing
        logger.exception("failed to tag documents for product isolation")
