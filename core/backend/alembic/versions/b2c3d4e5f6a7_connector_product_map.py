"""mynd Core: connector → product binding table

Adds ``mynd_shared.connector_product_map`` binding an Onyx connector (cc_pair)
to a product, enabling index-time document tagging for retrieval isolation
(plan §8.1/§8.2).

Idempotent (``IF NOT EXISTS``) so it is safe under Onyx's per-tenant migration
runs.

Revision ID: b2c3d4e5f6a7
Revises: 44068f1d3845
Create Date: 2026-06-27 00:00:01.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "44068f1d3845"
branch_labels = None
depends_on = None

SCHEMA = "mynd_shared"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.connector_product_map (
            cc_pair_id   INTEGER PRIMARY KEY,
            product_slug VARCHAR NOT NULL,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_connector_product_map_slug "
        f"ON {SCHEMA}.connector_product_map (product_slug)"
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.connector_product_map")
