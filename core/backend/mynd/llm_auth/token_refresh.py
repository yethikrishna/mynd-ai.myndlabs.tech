"""
Background refresh of OAuth credentials nearing expiry.

Runs as a Celery ``@shared_task`` (per Onyx conventions: shared_task, always
``expires=``). Wire it into a beat schedule, e.g. every 10 minutes:

    # in the mynd beat additions (see mynd/celery_schedule.py)
    "mynd-refresh-oauth-tokens": {
        "task": "mynd.refresh_oauth_tokens",
        "schedule": timedelta(minutes=10),
        "options": {"expires": 60 * 9},
    }

For each ``oauth_token`` credential whose access token expires within the
threshold, it uses the stored refresh token to obtain a new access token and
re-encrypts the payload. Tasks run in thread pools, so timeouts are enforced
in-task (short HTTP timeouts), not via Celery's time limits.
"""

from __future__ import annotations

import logging
import os
import time

import httpx
from celery import shared_task
from sqlalchemy import select

from onyx.db.engine.sql_engine import get_session_with_current_tenant

from mynd.db.models import CredentialType
from mynd.db.models import UserLLMCredential
from mynd.llm_auth.crypto import decrypt_payload
from mynd.llm_auth.crypto import encrypt_payload
from mynd.llm_auth.oauth_handlers import _provider_config

logger = logging.getLogger("mynd.token_refresh")

# Refresh tokens expiring within this many seconds.
REFRESH_THRESHOLD_SECONDS = int(
    os.environ.get("MYND_OAUTH_REFRESH_THRESHOLD_SECONDS", str(15 * 60))
)


def _expires_soon(payload: dict) -> bool:
    obtained = payload.get("_obtained_at")
    expires_in = payload.get("expires_in")
    if not obtained or not expires_in:
        # Unknown expiry — refresh opportunistically if we have a refresh token.
        return bool(payload.get("refresh_token"))
    return (obtained + expires_in - time.time()) <= REFRESH_THRESHOLD_SECONDS


def _refresh_one(provider: str, payload: dict) -> dict | None:
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        return None
    cfg = _provider_config(provider)
    resp = httpx.post(
        cfg.token_url,
        data={
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    tokens = resp.json()
    new_payload = dict(payload)
    new_payload["access_token"] = tokens.get("access_token", payload.get("access_token"))
    if tokens.get("refresh_token"):
        new_payload["refresh_token"] = tokens["refresh_token"]
    new_payload["expires_in"] = tokens.get("expires_in", payload.get("expires_in"))
    new_payload["_obtained_at"] = time.time()
    return new_payload


@shared_task(name="mynd.refresh_oauth_tokens", ignore_result=True)
def refresh_oauth_tokens() -> int:
    """Refresh all OAuth credentials that are close to expiry. Returns count."""
    refreshed = 0
    with get_session_with_current_tenant() as db:
        rows = (
            db.execute(
                select(UserLLMCredential).where(
                    UserLLMCredential.credential_type == CredentialType.OAUTH_TOKEN
                )
            )
            .scalars()
            .all()
        )
        for cred in rows:
            try:
                payload = decrypt_payload(cred.encrypted_payload)
                if not _expires_soon(payload):
                    continue
                new_payload = _refresh_one(cred.provider_name, payload)
                if new_payload is None:
                    continue
                cred.encrypted_payload = encrypt_payload(new_payload)
                db.add(cred)
                db.commit()
                refreshed += 1
            except Exception:  # noqa: BLE001 - one bad token must not stop the rest
                db.rollback()
                logger.exception(
                    "failed to refresh oauth token for cred %s (%s)",
                    cred.id,
                    cred.provider_name,
                )
    if refreshed:
        logger.info("refreshed %d oauth credential(s)", refreshed)
    return refreshed
