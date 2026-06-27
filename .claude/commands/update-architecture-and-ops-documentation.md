---
name: update-architecture-and-ops-documentation
description: Workflow command scaffold for update-architecture-and-ops-documentation in mynd-ai.myndlabs.tech.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /update-architecture-and-ops-documentation

Use this workflow when working on **update-architecture-and-ops-documentation** in `mynd-ai.myndlabs.tech`.

## Goal

Documents new features, deployment modes, or architectural changes in markdown and ops files.

## Common Files

- `ARCHITECTURE.md`
- `ops/deploy/README.md`
- `ops/deploy/*.yaml`
- `ops/deploy/Dockerfile.mynd`
- `ops/deploy/.env.example`
- `core/backend/mynd/README.md`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Update ARCHITECTURE.md with new features or deployment topologies
- Update or create ops/deploy/ files (Dockerfile, cloudrun-service, .env.example, README.md) as needed
- Update README.md files in relevant directories

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.