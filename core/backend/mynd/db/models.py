"""
SQLAlchemy models for the ``mynd_shared`` schema.

These tables augment Onyx without touching its CE/EE tables. They reuse Onyx's
declarative ``Base`` (so they participate in the same metadata / Alembic
autogenerate) but pin themselves to the ``mynd_shared`` schema.

Tables
------
- product_sessions      : per-product session tracking that wraps Onyx auth
- product_audit_logs    : per-product audit trail
- user_llm_credentials  : user-scoped LLM credentials (BYO key / OAuth)
- org_llm_credentials   : org-scoped LLM credentials

The ``encrypted_payload`` columns never store plaintext secrets — see
``mynd.llm_auth.crypto`` for the envelope-encryption helpers.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Index
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

# Reuse Onyx's declarative base so everything shares one MetaData object.
from onyx.db.models import Base

from mynd import MYND_SHARED_SCHEMA


class CredentialScope:
    """String constants for where an LLM credential came from."""

    SYSTEM = "system"
    ORG = "org"
    USER = "user"


class CredentialType:
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    GCP_SERVICE_ACCOUNT = "gcp_service_account"
    AWS_KEYS = "aws_keys"


class ProductSession(Base):
    """Cross-product session record. One row per (user, product) login.

    Onyx still owns the actual auth token/cookie; this table only records the
    product context so we can do per-product analytics, idle tracking and
    cross-product single-sign-on UX.
    """

    __tablename__ = "product_sessions"
    __table_args__ = {"schema": MYND_SHARED_SCHEMA}

    session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    product_slug: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)


class ProductAuditLog(Base):
    """Append-only per-product audit trail.

    Significant actions (chat, RAG query, connector fetch, admin change, …)
    write one row here via ``mynd.auth.audit.log_product_action``.
    """

    __tablename__ = "product_audit_logs"
    __table_args__ = (
        Index("ix_product_audit_logs_slug_ts", "product_slug", "timestamp"),
        {"schema": MYND_SHARED_SCHEMA},
    )

    log_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    org_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    product_slug: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String)
    resource_type: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    # one of CredentialScope.{SYSTEM,ORG,USER}
    llm_credential_scope: Mapped[str | None] = mapped_column(String, nullable=True)


class _LLMCredentialMixin:
    """Shared columns for user/org credential tables."""

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_slug: Mapped[str] = mapped_column(String, index=True)
    provider_name: Mapped[str] = mapped_column(String)
    # one of CredentialType.*
    credential_type: Mapped[str] = mapped_column(String)
    # KMS-wrapped secret material — never plaintext. See mynd.llm_auth.crypto.
    encrypted_payload: Mapped[bytes] = mapped_column(LargeBinary)
    # Optional custom/base URL for OpenAI-compatible proxies & local endpoints.
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserLLMCredential(_LLMCredentialMixin, Base):
    __tablename__ = "user_llm_credentials"
    __table_args__ = (
        Index(
            "ix_user_llm_cred_lookup",
            "user_id",
            "product_slug",
            "provider_name",
        ),
        {"schema": MYND_SHARED_SCHEMA},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), index=True)


class OrgLLMCredential(_LLMCredentialMixin, Base):
    __tablename__ = "org_llm_credentials"
    __table_args__ = (
        Index(
            "ix_org_llm_cred_lookup",
            "org_id",
            "product_slug",
            "provider_name",
        ),
        {"schema": MYND_SHARED_SCHEMA},
    )

    org_id: Mapped[str] = mapped_column(String, index=True)
