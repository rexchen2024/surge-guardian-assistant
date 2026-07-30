#!/bin/bash
set -euo pipefail

REPO_URL="${SURGE_SENTRY_REPO_URL:-${SGA_REPO_URL:-https://github.com/rexchen1803/surge-sentry.git}}"
INSTALL_DIR="${SURGE_SENTRY_HOME:-${SGA_HOME:-$HOME/.surge-sentry}}"
RUN_SETUP=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --setup)
      RUN_SETUP=1
      shift
      ;;
    *)
      echo "usage: install.sh [--dir PATH] [--setup]" >&2
      exit 2
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to install Surge Sentry" >&2
  exit 1
fi

if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only
elif [ -e "$INSTALL_DIR" ]; then
  echo "$INSTALL_DIR exists but is not a git checkout" >&2
  exit 1
else
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
scripts/surge-sentry version
scripts/surge-sentry doctor || true

if [ "$RUN_SETUP" -eq 1 ]; then
  scripts/surge-sentry setup --print-hermes-command
else
  cat <<EOF

Next:
  cd "$INSTALL_DIR"
  scripts/surge-sentry setup --print-hermes-command

Automatic updates:
  Normal tick runs check GitHub once a day.

Manual update:
  cd "$INSTALL_DIR"
  scripts/surge-sentry update

Send feedback:
  cd "$INSTALL_DIR"
  scripts/surge-sentry feedback --github-url
EOF
fi
