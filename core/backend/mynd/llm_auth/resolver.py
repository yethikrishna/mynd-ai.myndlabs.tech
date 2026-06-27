"""
Credential resolution for inference.

When any code path needs to talk to an LLM provider, it asks the resolver for
the credential to use. Precedence (highest first):

    1. user_llm_credentials   (this user, product, provider, is_default)
    2. org_llm_credentials    (this org,  product, provider, is_default)
    3. Onyx system provider    (existing onyx.db.llm admin configuration)

The resolved credential reports its ``scope`` so the audit log can record
whether a user key, org key, or the platform key served the request.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from mynd.db.models import CredentialScope
from mynd.db.models import OrgLLMCredential
from mynd.db.models import UserLLMCredential
from mynd.llm_auth.crypto import decrypt_payload


@dataclass
class ResolvedCredential:
    provider_name: str
    scope: str  # CredentialScope.{USER,ORG,SYSTEM}
    # Decrypted secret material (api_key / oauth tokens / service-account json).
    # Empty for SYSTEM scope — callers fall back to Onyx's own provider config.
    payload: dict
    base_url: str | None = None
    credential_type: str | None = None


def _select_default(db: Session, stmt) -> object | None:
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return None
    # Prefer the explicit default; otherwise the most recently updated.
    for row in rows:
        if getattr(row, "is_default", False):
            return row
    return sorted(rows, key=lambda r: r.updated_at, reverse=True)[0]


def resolve_llm_credential(
    db: Session,
    *,
    provider_name: str,
    product_slug: str,
    user_id: uuid.UUID | None,
    org_id: str | None,
) -> ResolvedCredential:
    # 1. user scope
    if user_id is not None:
        user_cred = _select_default(
            db,
            select(UserLLMCredential)
            .where(UserLLMCredential.user_id == user_id)
            .where(UserLLMCredential.product_slug == product_slug)
            .where(UserLLMCredential.provider_name == provider_name),
        )
        if user_cred is not None:
            return ResolvedCredential(
                provider_name=provider_name,
                scope=CredentialScope.USER,
                payload=decrypt_payload(user_cred.encrypted_payload),
                base_url=user_cred.base_url,
                credential_type=user_cred.credential_type,
            )

    # 2. org scope
    if org_id is not None:
        org_cred = _select_default(
            db,
            select(OrgLLMCredential)
            .where(OrgLLMCredential.org_id == org_id)
            .where(OrgLLMCredential.product_slug == product_slug)
            .where(OrgLLMCredential.provider_name == provider_name),
        )
        if org_cred is not None:
            return ResolvedCredential(
                provider_name=provider_name,
                scope=CredentialScope.ORG,
                payload=decrypt_payload(org_cred.encrypted_payload),
                base_url=org_cred.base_url,
                credential_type=org_cred.credential_type,
            )

    # 3. system scope — defer to Onyx's existing admin-configured provider.
    return ResolvedCredential(
        provider_name=provider_name,
        scope=CredentialScope.SYSTEM,
        payload={},
        base_url=None,
        credential_type=None,
    )
