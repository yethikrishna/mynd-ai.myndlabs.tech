---
name: add-backend-feature-with-api-and-admin-endpoints
description: Workflow command scaffold for add-backend-feature-with-api-and-admin-endpoints in mynd-ai.myndlabs.tech.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-backend-feature-with-api-and-admin-endpoints

Use this workflow when working on **add-backend-feature-with-api-and-admin-endpoints** in `mynd-ai.myndlabs.tech`.

## Goal

Implements a new backend feature, including business logic, API endpoints (often admin-gated), and related documentation.

## Common Files

- `core/backend/mynd/server/product_api.py`
- `core/backend/mynd/llm_auth/router.py`
- `core/backend/mynd/db/*.py`
- `core/backend/mynd/isolation/*.py`
- `core/backend/alembic/versions/*.py`
- `ARCHITECTURE.md`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Implement core logic in a new or existing backend Python module under core/backend/mynd/ or core/backend/mynd/db/
- Add or update API endpoints in core/backend/mynd/server/product_api.py or core/backend/mynd/llm_auth/router.py
- If needed, add helper functions or models in core/backend/mynd/db/ or core/backend/mynd/isolation/
- Update or create migration scripts if the database schema changes (core/backend/alembic/versions/)
- Update documentation in ARCHITECTURE.md and/or core/backend/mynd/README.md

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.