"""
OAuth connections to model providers (where the provider supports it, e.g.
Vertex AI via Google identity).

Callback URL convention:
    https://ai.myndlabs.tech/oauth/callback/<provider>

Flow:
    1. UI hits  GET  /api/llm-credentials/oauth/<provider>/start
       -> we return the provider authorize URL (client_id, redirect_uri, scope).
    2. Provider redirects to /oauth/callback/<provider>?code=...
       -> handle_oauth_callback exchanges code -> tokens, encrypts + stores them
          as a user_llm_credentials row (credential_type=oauth_token).

A background worker (mynd.llm_auth.token_refresh — see TODO) refreshes tokens
nearing expiry using the stored refresh_token.

Provider client registration (client_id/secret/scopes/endpoints) is read from
environment so secrets never live in the repo:
    MYND_OAUTH_<PROVIDER>_CLIENT_ID
    MYND_OAUTH_<PROVIDER>_CLIENT_SECRET
    MYND_OAUTH_<PROVIDER>_AUTH_URL
    MYND_OAUTH_<PROVIDER>_TOKEN_URL
    MYND_OAUTH_<PROVIDER>_SCOPES   (space-separated)
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from mynd.db.models import CredentialType
from mynd.db.models import UserLLMCredential
from mynd.llm_auth.crypto import encrypt_payload

OAUTH_CALLBACK_BASE = os.environ.get(
    "MYND_OAUTH_CALLBACK_BASE", "https://ai.myndlabs.tech/oauth/callback"
)


@dataclass
class OAuthProviderConfig:
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scopes: str


def _provider_config(provider: str) -> OAuthProviderConfig:
    p = provider.upper()
    try:
        return OAuthProviderConfig(
            client_id=os.environ[f"MYND_OAUTH_{p}_CLIENT_ID"],
            client_secret=os.environ[f"MYND_OAUTH_{p}_CLIENT_SECRET"],
            auth_url=os.environ[f"MYND_OAUTH_{p}_AUTH_URL"],
            token_url=os.environ[f"MYND_OAUTH_{p}_TOKEN_URL"],
            scopes=os.environ.get(f"MYND_OAUTH_{p}_SCOPES", ""),
        )
    except KeyError as exc:  # pragma: no cover
        raise RuntimeError(
            f"OAuth provider '{provider}' is not configured: missing {exc}"
        ) from exc


def build_authorize_url(provider: str, state: str) -> str:
    cfg = _provider_config(provider)
    params = {
        "client_id": cfg.client_id,
        "redirect_uri": f"{OAUTH_CALLBACK_BASE}/{provider}",
        "response_type": "code",
        "scope": cfg.scopes,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{cfg.auth_url}?{urlencode(params)}"


def handle_oauth_callback(
    db: Session,
    *,
    provider: str,
    code: str,
    user_id: uuid.UUID,
    product_slug: str,
) -> UserLLMCredential:
    """Exchange the auth code for tokens and persist them encrypted."""
    cfg = _provider_config(provider)
    resp = httpx.post(
        cfg.token_url,
        data={
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{OAUTH_CALLBACK_BASE}/{provider}",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    tokens = resp.json()

    payload = {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens.get("expires_in"),
        "token_type": tokens.get("token_type"),
        "scope": tokens.get("scope"),
    }

    # New OAuth connection becomes the default for this provider+product+user.
    db.query(UserLLMCredential).filter(
        UserLLMCredential.user_id == user_id,
        UserLLMCredential.product_slug == product_slug,
        UserLLMCredential.provider_name == provider,
    ).update({UserLLMCredential.is_default: False})

    cred = UserLLMCredential(
        user_id=user_id,
        product_slug=product_slug,
        provider_name=provider,
        credential_type=CredentialType.OAUTH_TOKEN,
        encrypted_payload=encrypt_payload(payload),
        is_default=True,
    )
    db.add(cred)
    db.commit()
    return cred
