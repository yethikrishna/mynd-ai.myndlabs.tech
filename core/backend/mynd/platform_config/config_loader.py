"""
Per-product configuration loader.

Products are defined entirely in the repo-root ``config/<slug>/`` directory as
YAML (zero code required to add one). This module discovers those directories
and parses them into typed ``ProductConfig`` objects that the backend and the
``/api/config/<slug>`` endpoint serve to the frontend.

Resolution of the config root, in order:
1. ``MYND_CONFIG_DIR`` environment variable (used in containers/tests)
2. the repo-root ``config/`` directory, located relative to this file
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import yaml


def _config_root() -> Path:
    env = os.environ.get("MYND_CONFIG_DIR")
    if env:
        return Path(env)
    # this file: core/backend/mynd/platform_config/config_loader.py
    # repo root:  parents[4]  -> core/backend/mynd/platform_config -> .. x4
    return Path(__file__).resolve().parents[4] / "config"


@dataclass
class Branding:
    primary_color: str = "#2563EB"
    logo: str = ""
    marketing_tagline: str = ""


@dataclass
class ProductConfig:
    slug: str
    name: str
    description: str = ""
    branding: Branding = field(default_factory=Branding)
    enabled_connectors: list[str] = field(default_factory=list)
    default_llm_providers: list[str] = field(default_factory=list)
    features: dict[str, bool] = field(default_factory=dict)
    # Raw parsed YAML for the auxiliary files, kept as-is for consumers.
    rbac: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, Any] = field(default_factory=dict)
    connectors: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        """The subset safe to ship to the browser via /api/config/<slug>."""
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "branding": {
                "primary_color": self.branding.primary_color,
                "logo": self.branding.logo,
                "marketing_tagline": self.branding.marketing_tagline,
            },
            "enabled_connectors": self.enabled_connectors,
            "default_llm_providers": self.default_llm_providers,
            "features": self.features,
        }


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def list_product_slugs() -> list[str]:
    root = _config_root()
    if not root.exists():
        return []
    return sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and (p / "product.yaml").exists()
    )


@functools.lru_cache(maxsize=64)
def get_product_config(slug: str) -> ProductConfig | None:
    root = _config_root()
    pdir = root / slug
    product_yaml = _read_yaml(pdir / "product.yaml")
    if not product_yaml:
        return None

    b = product_yaml.get("branding", {}) or {}
    return ProductConfig(
        slug=product_yaml.get("slug", slug),
        name=product_yaml.get("name", slug),
        description=product_yaml.get("description", ""),
        branding=Branding(
            primary_color=b.get("primary_color", "#2563EB"),
            logo=b.get("logo", ""),
            marketing_tagline=b.get("marketing_tagline", ""),
        ),
        enabled_connectors=product_yaml.get("enabled_connectors", []) or [],
        default_llm_providers=product_yaml.get("default_llm_providers", []) or [],
        features=product_yaml.get("features", {}) or {},
        rbac=_read_yaml(pdir / "rbac.yaml"),
        agents=_read_yaml(pdir / "agents.yaml"),
        connectors=_read_yaml(pdir / "connectors.yaml"),
    )


def clear_cache() -> None:
    """Drop the memoized configs (call after editing config on disk)."""
    get_product_config.cache_clear()
