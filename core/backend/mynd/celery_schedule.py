"""
Beat schedule additions contributed by the mynd layer.

Merge ``MYND_BEAT_SCHEDULE`` into Onyx's Celery beat schedule (Onyx uses a
DynamicTenantScheduler; in multi-tenant mode the scheduler fans these out per
tenant). Every entry sets ``expires`` per Onyx conventions so the queue can
never grow unbounded.
"""

from __future__ import annotations

from datetime import timedelta

MYND_BEAT_SCHEDULE: dict = {
    "mynd-refresh-oauth-tokens": {
        "task": "mynd.refresh_oauth_tokens",
        "schedule": timedelta(minutes=10),
        "options": {"expires": 60 * 9},
    },
}
