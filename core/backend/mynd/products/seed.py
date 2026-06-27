"""
CLI entry point to seed product agents into Onyx personas.

    python -m mynd.products.seed

Runs within the current tenant context. In multi-tenant deployments, invoke per
tenant (the deploy pipeline already iterates tenants for Alembic).
"""

from __future__ import annotations

import logging

from onyx.db.engine.sql_engine import get_session_with_current_tenant

from mynd.products.agent_seeder import sync_product_agents

logging.basicConfig(level=logging.INFO)


def main() -> None:
    with get_session_with_current_tenant() as db:
        count = sync_product_agents(db)
    print(f"Seeded {count} product persona(s).")


if __name__ == "__main__":
    main()
