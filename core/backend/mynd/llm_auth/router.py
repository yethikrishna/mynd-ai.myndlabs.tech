"""
FastAPI router for LLM credentials (user + org) and OAuth connections.

Mounted into the Onyx app by ``mynd.integration``. Endpoints:

    GET    /api/llm-credentials/providers          provider metadata for the UI
    POST   /api/llm-credentials/user               store/replace a BYO key
    GET    /api/llm-credentials/user               list (redacted) user creds
    DELETE /api/llm-credentials/user/{cred_id}     remove a user cred
    POST   /api/llm-credentials/org                (admin) store an org key
    GET    /api/llm-credentials/org                (admin) list org creds
    DELETE /api/llm-credentials/org/{cred_id}      (admin) remove an org cred
    GET    /api/llm-credentials/oauth/{provider}/start   begin OAuth
    GET    /oauth/callback/{provider}              OAuth redirect target

Auth: reuses Onyx's ``current_user`` / ``current_curator_or_admin_user`` deps —
no parallel auth. Secrets are encrypted at rest via ``mynd.llm_auth.crypto`` and
never returned. Follows Onyx conventions: no ``response_model=``, ``OnyxError``.
"""

from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from onyx.auth.users import current_curator_or_admin_user
from onyx.auth.users import current_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User
from onyx.error_handling.error_codes import OnyxErrorCode
from onyx.error_handling.exceptions import OnyxError
from onyx.llm.constants import LlmProviderNames

from mynd.db.models import CredentialType
from mynd.db.models import OrgLLMCredential
from mynd.db.models import UserLLMCredential
from mynd.dependencies import MyndContext
from mynd.dependencies import bind_request_context
from mynd.llm_auth import oauth_handlers
from mynd.llm_auth.crypto import encrypt_payload
from mynd.routing.product_router import get_product_slug

router = APIRouter(prefix="/api/llm-credentials", tags=["mynd-llm-credentials"])
oauth_callback_router = APIRouter(prefix="/oauth", tags=["mynd-oauth"])

# Providers that accept a custom base URL (OpenAI-compatible / proxy / local).
_BASE_URL_PROVIDERS = {
    LlmProviderNames.OPENAI_COMPATIBLE.value,
    LlmProviderNames.LITELLM_PROXY.value,
    LlmProviderNames.OLLAMA_CHAT.value,
    LlmProviderNames.LM_STUDIO.value,
    LlmProviderNames.OPENROUTER.value,
    LlmProviderNames.BIFROST.value,
}
# Providers that support an OAuth "Connect" flow.
_OAUTH_PROVIDERS = {LlmProviderNames.VERTEX_AI.value}


class UserCredentialRequest(BaseModel):
    provider_name: str
    credential_type: str = CredentialType.API_KEY
    api_key: str | None = None
    base_url: str | None = None
    # Free-form extra secret material (e.g. service-account JSON, aws keys).
    extra: dict | None = None
    is_default: bool = True


class OrgCredentialRequest(UserCredentialRequest):
    pass


class CredentialResponse(BaseModel):
    id: uuid.UUID
    provider_name: str
    credential_type: str
    base_url: str | None
    is_default: bool


def _require_slug(request: Request) -> str:
    slug = get_product_slug(request)
    if not slug:
        raise OnyxError(
            OnyxErrorCode.INVALID_INPUT, "Request is not scoped to a product."
        )
    return slug


def _to_response(cred: UserLLMCredential | OrgLLMCredential) -> CredentialResponse:
    return CredentialResponse(
        id=cred.id,
        provider_name=cred.provider_name,
        credential_type=cred.credential_type,
        base_url=cred.base_url,
        is_default=cred.is_default,
    )


def _build_payload(body: UserCredentialRequest) -> dict:
    payload: dict = dict(body.extra or {})
    if body.api_key:
        payload["api_key"] = body.api_key
    if not payload:
        raise OnyxError(
            OnyxErrorCode.MISSING_REQUIRED_FIELD, "No secret material provided."
        )
    return payload


# --------------------------------------------------------------------------- #
# Provider metadata
# --------------------------------------------------------------------------- #
@router.get("/providers")
def list_providers() -> dict:
    """Describe selectable providers for the BYO-key UI."""
    providers = []
    for p in LlmProviderNames:
        providers.append(
            {
                "name": p.value,
                "supports_base_url": p.value in _BASE_URL_PROVIDERS,
                "supports_oauth": p.value in _OAUTH_PROVIDERS,
            }
        )
    return {"providers": providers}


# --------------------------------------------------------------------------- #
# User-scoped credentials
# --------------------------------------------------------------------------- #
@router.post("/user")
def upsert_user_credential(
    body: UserCredentialRequest,
    ctx: MyndContext = Depends(bind_request_context),
    db: Session = Depends(get_session),
) -> CredentialResponse:
    slug = ctx.product_slug
    if not slug:
        raise OnyxError(OnyxErrorCode.INVALID_INPUT, "Not scoped to a product.")
    payload = _build_payload(body)

    if body.is_default:
        db.query(UserLLMCredential).filter(
            UserLLMCredential.user_id == ctx.user.id,
            UserLLMCredential.product_slug == slug,
            UserLLMCredential.provider_name == body.provider_name,
        ).update({UserLLMCredential.is_default: False})

    cred = UserLLMCredential(
        user_id=ctx.user.id,
        product_slug=slug,
        provider_name=body.provider_name,
        credential_type=body.credential_type,
        encrypted_payload=encrypt_payload(payload),
        base_url=body.base_url,
        is_default=body.is_default,
    )
    db.add(cred)
    db.commit()
    return _to_response(cred)


@router.get("/user")
def list_user_credentials(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> list[CredentialResponse]:
    slug = _require_slug(request)
    rows = (
        db.execute(
            select(UserLLMCredential)
            .where(UserLLMCredential.user_id == user.id)
            .where(UserLLMCredential.product_slug == slug)
        )
        .scalars()
        .all()
    )
    return [_to_response(r) for r in rows]


@router.delete("/user/{cred_id}", status_code=204)
def delete_user_credential(
    cred_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> None:
    cred = db.get(UserLLMCredential, cred_id)
    if cred is None or cred.user_id != user.id:
        raise OnyxError(OnyxErrorCode.CREDENTIAL_NOT_FOUND, "Credential not found.")
    db.delete(cred)
    db.commit()


# --------------------------------------------------------------------------- #
# Org-scoped credentials (admin / curator only)
# --------------------------------------------------------------------------- #
@router.post("/org")
def upsert_org_credential(
    body: OrgCredentialRequest,
    ctx: MyndContext = Depends(bind_request_context),
    _admin: User = Depends(current_curator_or_admin_user),
    db: Session = Depends(get_session),
) -> CredentialResponse:
    slug = ctx.product_slug
    if not slug:
        raise OnyxError(OnyxErrorCode.INVALID_INPUT, "Not scoped to a product.")
    if not ctx.org_id:
        raise OnyxError(
            OnyxErrorCode.INVALID_INPUT, "No org context for this request."
        )
    payload = _build_payload(body)

    if body.is_default:
        db.query(OrgLLMCredential).filter(
            OrgLLMCredential.org_id == ctx.org_id,
            OrgLLMCredential.product_slug == slug,
            OrgLLMCredential.provider_name == body.provider_name,
        ).update({OrgLLMCredential.is_default: False})

    cred = OrgLLMCredential(
        org_id=ctx.org_id,
        product_slug=slug,
        provider_name=body.provider_name,
        credential_type=body.credential_type,
        encrypted_payload=encrypt_payload(payload),
        base_url=body.base_url,
        is_default=body.is_default,
    )
    db.add(cred)
    db.commit()
    return _to_response(cred)


@router.get("/org")
def list_org_credentials(
    ctx: MyndContext = Depends(bind_request_context),
    _admin: User = Depends(current_curator_or_admin_user),
    db: Session = Depends(get_session),
) -> list[CredentialResponse]:
    if not ctx.product_slug or not ctx.org_id:
        return []
    rows = (
        db.execute(
            select(OrgLLMCredential)
            .where(OrgLLMCredential.org_id == ctx.org_id)
            .where(OrgLLMCredential.product_slug == ctx.product_slug)
        )
        .scalars()
        .all()
    )
    return [_to_response(r) for r in rows]


@router.delete("/org/{cred_id}", status_code=204)
def delete_org_credential(
    cred_id: uuid.UUID,
    ctx: MyndContext = Depends(bind_request_context),
    _admin: User = Depends(current_curator_or_admin_user),
    db: Session = Depends(get_session),
) -> None:
    cred = db.get(OrgLLMCredential, cred_id)
    if cred is None or cred.org_id != ctx.org_id:
        raise OnyxError(OnyxErrorCode.CREDENTIAL_NOT_FOUND, "Credential not found.")
    db.delete(cred)
    db.commit()


# --------------------------------------------------------------------------- #
# OAuth
# --------------------------------------------------------------------------- #
@router.get("/oauth/{provider}/start")
def start_oauth(
    provider: str,
    request: Request,
    user: User = Depends(current_user),
) -> dict:
    _require_slug(request)
    # In production, persist `state` (CSRF + slug + user) in a short-lived store.
    state = secrets.token_urlsafe(24)
    return {"authorize_url": oauth_handlers.build_authorize_url(provider, state)}


@oauth_callback_router.get("/callback/{provider}")
def oauth_callback(
    provider: str,
    code: str,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> RedirectResponse:
    slug = get_product_slug(request) or "eng"
    oauth_handlers.handle_oauth_callback(
        db, provider=provider, code=code, user_id=user.id, product_slug=slug
    )
    return RedirectResponse(url=f"/{slug}/settings/models?connected={provider}")
