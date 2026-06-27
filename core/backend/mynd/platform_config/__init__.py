"""Global + per-product configuration loading for mynd Core."""

from mynd.platform_config.config_loader import ProductConfig
from mynd.platform_config.config_loader import get_product_config
from mynd.platform_config.config_loader import list_product_slugs

__all__ = ["ProductConfig", "get_product_config", "list_product_slugs"]
