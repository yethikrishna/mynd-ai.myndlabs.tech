# Licensing notes

This repository combines original Mynd Labs work with a fork of Onyx. This file
records exactly what is licensed how, so there is no ambiguity.

## 1. Mynd Labs original work — MIT

The code authored by Mynd Labs (the `mynd` backend layer under
`core/backend/mynd/`, plus `config/`, `overlay/`, and `ops/`) is licensed under
the MIT License in [`LICENSE`](./LICENSE).

## 2. Onyx fork under `core/` — mixed, as shipped by upstream

`core/` is a fork of [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx).

- **Upstream commit forked:** `e38153434b4bd6b77774b8da54747b39d2cc05e2`
  (recorded in `core/.onyx-upstream-commit`).
- Upstream Onyx is **dual-structured** (see `core/LICENSE`):
  - Everything **outside** `ee` directories is **MIT ("MIT Expat")**.
  - Everything **inside** `ee` directories is licensed under the **Onyx
    Enterprise License**, *not* MIT. The affected paths are:
    - `core/backend/ee/`
    - `core/web/src/app/ee/`
    - `core/web/src/ee/`
  - Each of those directories retains its own `LICENSE` file, unmodified.

> ⚠️ **Important — read before relying on this.**
> Upstream Onyx does **not** publish the `ee` code under MIT. The architecture
> plan for this project assumes Mynd Labs holds a **separate, written grant**
> from Onyx that relicenses the Community **and** Enterprise code to Mynd under
> MIT terms. That grant is a private agreement between Mynd Labs and Onyx and is
> **not** evidenced by the public upstream license. This repository therefore
> keeps the upstream `ee` license files in place and does **not** silently
> restamp the `ee` code as MIT. Do not remove or relicense the `ee` `LICENSE`
> files until the grant below is filled in and verified by counsel.

## 3. Onyx Enterprise grant (to be completed)

Fill this in with the actual grant evidence. Until then, treat the `ee` code as
governed by the Onyx Enterprise License.

| Field | Value |
| --- | --- |
| Granting entity | Onyx / DanswerAI, Inc. |
| Grant recipient | Mynd Labs |
| Scope | Community + Enterprise (`ee`) code, relicensed to MIT for Mynd |
| Grant date | _TODO_ |
| Onyx contact (name, email) | _TODO_ |
| Reference (email/contract ID, link to signed doc) | _TODO_ |
| Reviewed by counsel | _TODO_ |

## 4. Third-party dependencies

Onyx and the Mynd layer pull in third-party packages under their own licenses.
CI runs `ops/ci/license_scan.sh` to flag strong-copyleft licenses
(GPL/AGPL/LGPL-3/SSPL/CC-BY-NC) that would be incompatible with MIT
distribution. Wire it to real SBOM tooling (`pip-licenses`, `license-checker`)
before relying on it as a gate.
