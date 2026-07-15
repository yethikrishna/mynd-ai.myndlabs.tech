```markdown
# mynd-ai.myndlabs.tech Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill covers the core development conventions and workflows for the `mynd-ai.myndlabs.tech` repository. The codebase is primarily Python for backend logic, with a React-based frontend. There is no major framework detected for the backend, and the repository emphasizes modularity, clear API boundaries, and documentation-driven development. This guide will help contributors follow established patterns for backend and frontend feature development, as well as documentation and operational updates.

## Coding Conventions

### File Naming
- **Python:** Uses `camelCase` for file names.
  - Example: `productApi.py`, `llmAuthRouter.py`
- **Frontend (React):** Uses `camelCase` or PascalCase for components.
  - Example: `ProductContext.tsx`, `useProductSlug.ts`

### Import Style
- **Python:** Imports are typically aliased.
  ```python
  import core.backend.mynd.db.models as db_models
  import core.backend.mynd.isolation.helpers as iso_helpers
  ```
- **Frontend (React):**
  ```typescript
  import ProductContext from './ProductContext'
  import * as hooks from './hooks'
  ```

### Export Style
- **Mixed:** Both named and default exports are used in frontend code.
  ```typescript
  export default ProductContext
  export { useProductSlug }
  ```

### Commit Patterns
- **Type:** Freeform, no enforced prefix.
- **Average Length:** ~66 characters.

## Workflows

### add-backend-feature-with-api-and-admin-endpoints
**Trigger:** When you want to add a new backend capability or admin API endpoint.  
**Command:** `/new-api-endpoint`

1. Implement core logic in a new or existing backend Python module under `core/backend/mynd/` or `core/backend/mynd/db/`.
   ```python
   # core/backend/mynd/db/productLogic.py
   def create_product(...):
       # business logic here
   ```
2. Add or update API endpoints in `core/backend/mynd/server/product_api.py` or `core/backend/mynd/llm_auth/router.py`.
   ```python
   # core/backend/mynd/server/product_api.py
   @router.post("/products")
   def create_product_endpoint(...):
       ...
   ```
3. If needed, add helper functions or models in `core/backend/mynd/db/` or `core/backend/mynd/isolation/`.
4. Update or create migration scripts if the database schema changes (`core/backend/alembic/versions/`).
5. Update documentation in `ARCHITECTURE.md` and/or `core/backend/mynd/README.md`.

**Files Involved:**
- `core/backend/mynd/server/product_api.py`
- `core/backend/mynd/llm_auth/router.py`
- `core/backend/mynd/db/*.py`
- `core/backend/mynd/isolation/*.py`
- `core/backend/alembic/versions/*.py`
- `ARCHITECTURE.md`
- `core/backend/mynd/README.md`

---

### add-frontend-feature-or-app-shell
**Trigger:** When you want to add a new frontend page, shell, or UI component for a product.  
**Command:** `/new-frontend-feature`

1. Create or update React components in `core/web/src/mynd/components/` or `overlays/`.
   ```tsx
   // core/web/src/mynd/components/ProductCard.tsx
   export default function ProductCard({ product }) {
     return <div>{product.name}</div>
   }
   ```
2. Add or update route files in `core/web/src/app/[productSlug]/`.
3. Implement or modify hooks in `core/web/src/mynd/hooks.ts` or `useProductSlug.ts`.
   ```typescript
   // core/web/src/mynd/useProductSlug.ts
   export function useProductSlug() {
     // hook logic
   }
   ```
4. Update or create context providers in `core/web/src/mynd/ProductContext.tsx`.
5. Update documentation in `core/web/src/mynd/README.md`.

**Files Involved:**
- `core/web/src/mynd/components/*.tsx`
- `core/web/src/app/[productSlug]/**/*.tsx`
- `core/web/src/mynd/hooks.ts`
- `core/web/src/mynd/useProductSlug.ts`
- `core/web/src/mynd/ProductContext.tsx`
- `core/web/src/mynd/README.md`

---

### update-architecture-and-ops-documentation
**Trigger:** When you add a significant feature or deployment option that needs documentation.  
**Command:** `/update-docs`

1. Update `ARCHITECTURE.md` with new features or deployment topologies.
2. Update or create `ops/deploy/` files (`Dockerfile`, `cloudrun-service`, `.env.example`, `README.md`) as needed.
3. Update `README.md` files in relevant directories.

**Files Involved:**
- `ARCHITECTURE.md`
- `ops/deploy/README.md`
- `ops/deploy/*.yaml`
- `ops/deploy/Dockerfile.mynd`
- `ops/deploy/.env.example`
- `core/backend/mynd/README.md`
- `core/web/src/mynd/README.md`

---

## Testing Patterns

- **Framework:** Unknown (not detected).
- **Test File Pattern:** Files matching `*.test.*` (e.g., `productApi.test.py`, `ProductCard.test.tsx`).
- **Typical Usage:** Place test files alongside implementation or in dedicated test directories.
  ```python
  # core/backend/mynd/db/productLogic.test.py
  def test_create_product():
      ...
  ```
  ```typescript
  // core/web/src/mynd/components/ProductCard.test.tsx
  test('renders product name', () => {
    ...
  })
  ```

## Commands

| Command               | Purpose                                                        |
|-----------------------|----------------------------------------------------------------|
| /new-api-endpoint     | Start a new backend feature or admin API endpoint workflow     |
| /new-frontend-feature | Start a new frontend feature, page, or shell component         |
| /update-docs          | Update architecture and operational documentation              |
```
