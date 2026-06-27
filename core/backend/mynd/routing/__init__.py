"""Product-slug routing for mynd Core."""

from mynd.routing.product_router import KNOWN_PRODUCT_SLUGS
from mynd.routing.product_router import ProductContextMiddleware
from mynd.routing.product_router import get_product_slug

__all__ = [
    "ProductContextMiddleware",
    "get_product_slug",
    "KNOWN_PRODUCT_SLUGS",
]
