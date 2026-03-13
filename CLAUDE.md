# CLAUDE.md — Instructions for Claude Code Agent

## Read These First

- `AGENTS.md` — universal agent rules (MUST follow, covers all agents)
- `.github/copilot-instructions.md` — operating rules (MUST follow)
- `docs/CODING_STYLE.md` — code style guide (MUST follow)

## Project Overview

CPU temperature monitor and IPMI fan speed controller for Supermicro
servers.  Uses Rich for terminal UI, ipmitool for fan control, runs
as a systemd service inside tmux.

## Stack

Python 3.11, Rich, ipmitool, systemd, tmux

## Key Commands

- Verify (lint + test): `make verify`
- Lint only: `make lint`
- Format: `make fmt`
- Test only: `make test`

## Hard Rules (non-negotiable)

1. **No CLI command > 80 characters.** Use cantrips + Makefile aliases.
2. **Run verification before claiming done.** Iterate until green.
3. **Long descriptive names.** Verbose teaching comments are welcome.
4. **Small diffs.** Prefer < 300 lines. Split larger work into slices.
5. **IPMI safety.** Never set fan speed below 0x09. Always enforce
   100% at DANGER_TEMP.

## File Layout

```
cputemp.py             # Main script — monitor + fan control
requirements.txt       # Python dependencies
systemd/
  cputemp.service      # systemd unit file
cantrips/              # Automation scripts
docs/                  # Documentation
sessions/              # Session close-out logs
```

## Before You Start Any Task

1. Read the mandatory docs listed above
2. Run `make verify` to confirm baseline is green
3. Understand the scope before editing
