#!/bin/bash
set -euo pipefail

REPO_URL="${SGA_REPO_URL:-https://github.com/rexchen2024/surge-guardian-assistant.git}"
INSTALL_DIR="${SGA_HOME:-$HOME/.surge-guardian-assistant}"
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
  echo "git is required to install Surge 守护助手" >&2
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
scripts/surge-guardian-assistant version
scripts/surge-guardian-assistant doctor || true

if [ "$RUN_SETUP" -eq 1 ]; then
  scripts/surge-guardian-assistant setup --print-hermes-command
else
  cat <<EOF

Next:
  cd "$INSTALL_DIR"
  scripts/surge-guardian-assistant setup --print-hermes-command

Automatic updates:
  Normal tick runs check GitHub once a day.

Manual update:
  cd "$INSTALL_DIR"
  scripts/surge-guardian-assistant update

Send feedback:
  cd "$INSTALL_DIR"
  scripts/surge-guardian-assistant feedback --github-url
EOF
fi
