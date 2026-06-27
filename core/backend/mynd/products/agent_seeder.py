"""
Seed Onyx personas (agents) from each product's ``agents.yaml``.

Turns the config-only agent templates into real, listed Onyx personas tagged to
their product, so the per-product app shell can surface "enabled agents" that
actually work in Onyx's chat. Idempotent: existing product personas are updated
in place, not duplicated.

Personas are named ``[mynd:<slug>] <Agent Name>`` so they are:
  * easy to filter per product (prefix match)
  * unlikely to collide with user-created assistants

Run at deploy time (or on startup) via::

    python -m mynd.products.seed   # or scripts/seed_mynd_products.py

Tool wiring (mapping the template ``tools`` list to Onyx tool ids) is left as a
follow-up — personas are seeded with the default toolset until then.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from onyx.db.models import Persona
from onyx.db.persona import upsert_persona

from mynd.platform_config.config_loader import get_product_config
from mynd.platform_config.config_loader import list_product_slugs

logger = logging.getLogger("mynd.agent_seeder")

PERSONA_PREFIX = "[mynd:{slug}]"


def product_persona_name(slug: str, agent_name: str) -> str:
    return f"{PERSONA_PREFIX.format(slug=slug)} {agent_name}"


def _existing_persona(db: Session, name: str) -> Persona | None:
    return (
        db.query(Persona)
        .filter(Persona.name == name, Persona.deleted == False)  # noqa: E712
        .first()
    )


def sync_product_agents(db: Session) -> int:
    """Create/update personas for every product's configured agents.

    Returns the number of personas upserted.
    """
    upserted = 0
    for slug in list_product_slugs():
        config = get_product_config(slug)
        if config is None:
            continue
        agents = config.agents.get("agents", []) or []
        for agent in agents:
            agent_name = agent.get("name") or agent.get("key")
            if not agent_name:
                continue
            name = product_persona_name(slug, agent_name)
            description = agent.get("description", "") or ""

            existing = _existing_persona(db, name)
            try:
                upsert_persona(
                    user=None,  # system operation
                    name=name,
                    description=description,
                    starter_messages=None,
                    system_prompt=None,
                    task_prompt=None,
                    datetime_aware=None,
                    is_public=True,
                    db_session=db,
                    persona_id=existing.id if existing else None,
                    is_listed=True,
                    builtin_persona=False,
                    commit=False,
                )
                upserted += 1
            except Exception:  # noqa: BLE001 - one bad agent must not stop the rest
                db.rollback()
                logger.exception("failed to seed persona %s", name)
    db.commit()
    logger.info("seeded %d product persona(s)", upserted)
    return upserted
