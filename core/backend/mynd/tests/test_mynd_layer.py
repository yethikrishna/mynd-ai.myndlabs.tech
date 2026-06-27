"""
Unit tests for the mynd layer that do not require the full Onyx runtime.

Covered: product-slug extraction, config loading, and RBAC capability mapping.
DB-backed pieces (sessions, audit, credential resolver) are exercised by the
external-dependency-unit tests that run against a real Postgres.
"""

import os
from pathlib import Path

import pytest

# Point the config loader at the repo-root config/ regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault("MYND_CONFIG_DIR", str(_REPO_ROOT / "config"))

from mynd.auth.rbac import resolve_capabilities  # noqa: E402
from mynd.platform_config.config_loader import (  # noqa: E402
    get_product_config,
    list_product_slugs,
)
from mynd.routing.product_router import extract_slug_from_path  # noqa: E402

KNOWN = {"eng", "grc", "sales", "support", "people", "sre"}


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/eng/api/chat", "eng"),
        ("/grc", "grc"),
        ("/", None),
        ("", None),
        ("/api/health", None),  # reserved prefix
        ("/oauth/callback/vertex", None),  # reserved prefix
        ("/unknown-slug/x", None),  # not a known product
    ],
)
def test_extract_slug(path, expected):
    assert extract_slug_from_path(path, KNOWN) == expected


def test_all_products_discovered():
    assert set(list_product_slugs()) == KNOWN


def test_product_config_public_dict_is_browser_safe():
    cfg = get_product_config("eng")
    assert cfg is not None
    pub = cfg.public_dict()
    # Public payload exposes branding/features but not RBAC/connector internals.
    assert "branding" in pub and "features" in pub
    assert "rbac" not in pub and "connectors" not in pub


def test_rbac_exact_role_match():
    caps = resolve_capabilities("eng", "admin")
    assert "view_audit_logs" in caps
    assert "manage_llm_credentials" in caps


def test_rbac_onyx_basic_falls_back_to_member():
    # Onyx "basic" has no same-named product role, so it maps to "member".
    caps = resolve_capabilities("eng", "basic")
    assert caps == {"chat", "run_agents", "save_conversations"}


def test_rbac_unknown_product_is_empty():
    assert resolve_capabilities("does-not-exist", "admin") == set()
