---
name: add-frontend-feature-or-app-shell
description: Workflow command scaffold for add-frontend-feature-or-app-shell in mynd-ai.myndlabs.tech.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-frontend-feature-or-app-shell

Use this workflow when working on **add-frontend-feature-or-app-shell** in `mynd-ai.myndlabs.tech`.

## Goal

Implements a new frontend feature, page, or shell component for product-specific UI, often with hooks and context.

## Common Files

- `core/web/src/mynd/components/*.tsx`
- `core/web/src/app/[productSlug]/**/*.tsx`
- `core/web/src/mynd/hooks.ts`
- `core/web/src/mynd/useProductSlug.ts`
- `core/web/src/mynd/ProductContext.tsx`
- `core/web/src/mynd/README.md`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update React components in core/web/src/mynd/components/ or overlays/
- Add or update route files in core/web/src/app/[productSlug]/
- Implement or modify hooks in core/web/src/mynd/hooks.ts or useProductSlug.ts
- Update or create context providers in core/web/src/mynd/ProductContext.tsx
- Update documentation in core/web/src/mynd/README.md

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.