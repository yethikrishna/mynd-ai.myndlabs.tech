"""
Data isolation helpers (plan §8): index namespacing and connector scoping.

These keep one product's data from leaking into another's by deriving stable
namespaces from ``product_slug`` + ``org_id`` and by validating connector access
against each product's ``connectors.yaml``.
"""

from mynd.isolation.connector_isolation import allowed_connectors
from mynd.isolation.connector_isolation import connector_scopes
from mynd.isolation.connector_isolation import is_connector_allowed
from mynd.isolation.namespacing import index_namespace
from mynd.isolation.namespacing import retrieval_filter
from mynd.isolation.retrieval import apply_retrieval_isolation
from mynd.isolation.retrieval import product_document_tags

__all__ = [
    "index_namespace",
    "retrieval_filter",
    "allowed_connectors",
    "connector_scopes",
    "is_connector_allowed",
    "apply_retrieval_isolation",
    "product_document_tags",
]
