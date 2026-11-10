#!/usr/bin/env bash
# LAB-ONLY shortcut: lets the worker start the runner with `sudo -n` (no password).
# Run ONCE on your own WSL Ubuntu:   sudo bash scripts/setup_sudoers.sh
# It allows ONLY this one command, for ONLY your user:
#     .venv/bin/python -m runner.run_cli <file>
# Never do this on a shared or real server.
set -e
if [ "$EUID" -ne 0 ]; then echo "Run with sudo:  sudo bash scripts/setup_sudoers.sh"; exit 1; fi
USER_NAME="${SUDO_USER:-}"
if [ -z "$USER_NAME" ]; then echo "Cannot find your user name. Run it with sudo from your normal user."; exit 1; fi
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$REPO/.venv/bin/python"
if [ ! -x "$PY" ]; then echo "Missing $PY. Run 'make setup' first."; exit 1; fi
TMP="$(mktemp)"
echo "$USER_NAME ALL=(root) NOPASSWD: $PY -m runner.run_cli *" > "$TMP"
visudo -cf "$TMP"                     # check the syntax BEFORE installing it
install -m 0440 "$TMP" /etc/sudoers.d/codeexam-runner
rm -f "$TMP"
echo "Done. Test it with:  sudo -n $PY -m runner.run_cli examples/request1.json"
echo "To remove it later:  sudo rm /etc/sudoers.d/codeexam-runner"
