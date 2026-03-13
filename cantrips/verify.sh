#!/usr/bin/env bash
# CANTRIP: verify
# PURPOSE:
#   Run the full verification pipeline (lint + test) in one command.
#   This is the single source of truth for "is this code correct?"
#   Used by: developers, CI, AI agents.
#
# USAGE:
#   ./cantrips/verify.sh
#
# DEPENDENCIES:
#   - ruff (Python linter/formatter)
#   - pytest (test runner)
#   - Virtual environment at .venv/
#
# FUNCTIONS:
#   - run_step: Execute one verification step with pass/fail output
#   - main:     Orchestrate lint → test pipeline

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# --- Colors (skip if not a terminal) ---
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  RED='\033[0;31m'
  YELLOW='\033[1;33m'
  CYAN='\033[0;36m'
  RESET='\033[0m'
else
  GREEN='' RED='' YELLOW='' CYAN='' RESET=''
fi

run_step() {
  local label="$1"
  shift
  echo -e "\n${YELLOW}▶ ${label}${RESET}"
  if "$@"; then
    echo -e "${GREEN}  ✔ ${label} passed${RESET}"
  else
    echo -e "${RED}  ✘ ${label} failed${RESET}"
    echo -e "\n${RED}Verification FAILED.${RESET}"
    exit 1
  fi
}

main() {
  echo -e "${CYAN}═══════════════════════════════════════${RESET}"
  echo -e "${CYAN}  🧙 Cantrip: verify (lint + test)${RESET}"
  echo -e "${CYAN}═══════════════════════════════════════${RESET}"

  run_step "Lint"  .venv/bin/ruff check cputemp.py
  run_step "Test"  .venv/bin/pytest tests/ -v

  echo -e "\n${GREEN}✅ All checks passed!${RESET}"
}

main "$@"
