"""mynd Core: create mynd_shared schema (sessions, audit, llm credentials)

Adds the Mynd Labs layer's tables in a dedicated ``mynd_shared`` schema so they
never collide with Onyx CE/EE tables:

- product_sessions      : per-product session tracking wrapping Onyx auth
- product_audit_logs    : per-product audit trail
- user_llm_credentials  : user-scoped BYO LLM credentials / OAuth tokens
- org_llm_credentials   : org-scoped LLM credentials

Multi-tenant note: in cloud mode Alembic runs this once per tenant schema. The
shared schema and its tables are created with ``IF NOT EXISTS`` so repeated
invocations across tenant schemas are no-ops after the first.

Revision ID: a1b2c3d4e5f6
Revises: f3a9c1d4b7e2
Create Date: 2026-06-27 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f3a9c1d4b7e2"
branch_labels = None
depends_on = None

SCHEMA = "mynd_shared"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.product_sessions (
            session_id   UUID PRIMARY KEY,
            user_id      UUID NOT NULL,
            product_slug VARCHAR NOT NULL,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_active  TIMESTAMPTZ NOT NULL DEFAULT now(),
            ip_address   VARCHAR,
            user_agent   VARCHAR
        )
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_product_sessions_user_id "
        f"ON {SCHEMA}.product_sessions (user_id)"
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_product_sessions_slug "
        f"ON {SCHEMA}.product_sessions (product_slug)"
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.product_audit_logs (
            log_id               UUID PRIMARY KEY,
            timestamp            TIMESTAMPTZ NOT NULL DEFAULT now(),
            user_id              UUID,
            org_id               VARCHAR,
            product_slug         VARCHAR NOT NULL,
            action               VARCHAR NOT NULL,
            resource_type        VARCHAR,
            resource_id          VARCHAR,
            llm_provider         VARCHAR,
            llm_credential_scope VARCHAR
        )
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_product_audit_logs_slug_ts "
        f"ON {SCHEMA}.product_audit_logs (product_slug, timestamp)"
    )

    for table, owner_col in (
        ("user_llm_credentials", "user_id UUID NOT NULL"),
        ("org_llm_credentials", "org_id VARCHAR NOT NULL"),
    ):
        op.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{table} (
                id                UUID PRIMARY KEY,
                {owner_col},
                product_slug      VARCHAR NOT NULL,
                provider_name     VARCHAR NOT NULL,
                credential_type   VARCHAR NOT NULL,
                encrypted_payload BYTEA NOT NULL,
                base_url          VARCHAR,
                is_default        BOOLEAN NOT NULL DEFAULT false,
                created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )

    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_user_llm_cred_lookup "
        f"ON {SCHEMA}.user_llm_credentials (user_id, product_slug, provider_name)"
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_org_llm_cred_lookup "
        f"ON {SCHEMA}.org_llm_credentials (org_id, product_slug, provider_name)"
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.user_llm_credentials")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.org_llm_credentials")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.product_audit_logs")
    op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.product_sessions")
    # Schema intentionally left in place; it may be shared across tenants.
