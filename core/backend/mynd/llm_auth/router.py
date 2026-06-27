"""
FastAPI router for user-managed LLM credentials and OAuth connections.

Mounted into the Onyx app by ``mynd.integration``. Endpoints:

    POST   /api/llm-credentials/user            store/replace a BYO key
    GET    /api/llm-credentials/user            list (redacted) user creds
    DELETE /api/llm-credentials/user/{cred_id}  remove a user cred
    GET    /api/llm-credentials/oauth/{provider}/start   begin OAuth
    GET    /oauth/callback/{provider}            OAuth redirect target

Auth: reuses Onyx's ``current_user`` dependency — no parallel auth.
Secrets are encrypted at rest via ``mynd.llm_auth.crypto`` and never returned.

Follows Onyx conventions (see core/CLAUDE.md): no ``response_model=`` on routes,
errors raised as ``OnyxError`` rather than ``HTTPException``.
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

from onyx.auth.users import current_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User
from onyx.error_handling.error_codes import OnyxErrorCode
from onyx.error_handling.exceptions import OnyxError

from mynd.db.models import CredentialType
from mynd.db.models import UserLLMCredential
from mynd.llm_auth import oauth_handlers
from mynd.llm_auth.crypto import encrypt_payload
from mynd.routing.product_router import get_product_slug

router = APIRouter(prefix="/api/llm-credentials", tags=["mynd-llm-credentials"])
oauth_callback_router = APIRouter(prefix="/oauth", tags=["mynd-oauth"])


class UserCredentialRequest(BaseModel):
    provider_name: str
    credential_type: str = CredentialType.API_KEY
    api_key: str | None = None
    base_url: str | None = None
    # Free-form extra secret material (e.g. service-account JSON, aws keys).
    extra: dict | None = None
    is_default: bool = True


class UserCredentialResponse(BaseModel):
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


def _to_response(cred: UserLLMCredential) -> UserCredentialResponse:
    return UserCredentialResponse(
        id=cred.id,
        provider_name=cred.provider_name,
        credential_type=cred.credential_type,
        base_url=cred.base_url,
        is_default=cred.is_default,
    )


@router.post("/user")
def upsert_user_credential(
    body: UserCredentialRequest,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> UserCredentialResponse:
    slug = _require_slug(request)

    payload: dict = dict(body.extra or {})
    if body.api_key:
        payload["api_key"] = body.api_key
    if not payload:
        raise OnyxError(
            OnyxErrorCode.MISSING_REQUIRED_FIELD, "No secret material provided."
        )

    if body.is_default:
        db.query(UserLLMCredential).filter(
            UserLLMCredential.user_id == user.id,
            UserLLMCredential.product_slug == slug,
            UserLLMCredential.provider_name == body.provider_name,
        ).update({UserLLMCredential.is_default: False})

    cred = UserLLMCredential(
        user_id=user.id,
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
) -> list[UserCredentialResponse]:
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
