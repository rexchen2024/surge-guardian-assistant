#!/bin/bash
# Wrapper for the realtime guardian. Prints wakeAgent=false when silent.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

exec /usr/bin/python3 "${ROOT_DIR}/scripts/surge_realtime_guardian.py"

