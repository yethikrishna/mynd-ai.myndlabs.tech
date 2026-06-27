#!/usr/bin/env bash
# Fail the build if any transitive dependency carries a strong-copyleft license
# (GPL/AGPL/etc.), which would conflict with shipping mynd Core under MIT.
#
# This is a starting point: wire it to real SBOM tooling (pip-licenses for
# Python, license-checker for the JS workspace) in CI. Until those are added it
# prints guidance and exits 0 so it does not block the first builds.
set -euo pipefail

DISALLOWED='GPL-2.0|GPL-3.0|AGPL|LGPL-3.0|SSPL|CC-BY-NC'

echo "== mynd license scan =="

scan_python() {
  if command -v pip-licenses >/dev/null 2>&1; then
    echo "-- Python (pip-licenses) --"
    pip-licenses --format=csv --with-urls \
      | grep -Ei "$DISALLOWED" && { echo "Disallowed Python license found"; return 1; } || true
  else
    echo "pip-licenses not installed; skipping Python scan (add to CI deps)."
  fi
}

scan_node() {
  if command -v license-checker >/dev/null 2>&1; then
    echo "-- Node (license-checker) --"
    license-checker --summary --excludePrivatePackages \
      | grep -Ei "$DISALLOWED" && { echo "Disallowed Node license found"; return 1; } || true
  else
    echo "license-checker not installed; skipping Node scan (add to CI deps)."
  fi
}

scan_python
scan_node
echo "License scan complete."
