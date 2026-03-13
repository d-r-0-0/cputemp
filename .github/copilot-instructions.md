# Copilot Instructions

## Operating mode
- Default to: Explore → Plan → Implement → Verify.
- For non-trivial work, write a PLAN section before changing code.
- Prefer small, reviewable diffs and incremental commits.
- If requirements are unclear, ask questions before broad edits.

## Command-line rule (hard)
- NEVER execute or suggest a command longer than 80 characters.
- If a command would exceed 80 chars, create a "cantrip" script instead:
  - Put it in `cantrips/`
  - Add a short alias (Makefile target or `scripts/` wrapper) with a name <= 20 chars.
  - The alias command itself must be <= 80 chars.

## Verification loop (hard)
- Every time you claim "done", you MUST run verification:
  - `make verify` (preferred) OR the repo's documented test/lint/build commands.
- If verification fails, iterate until green.

## Coding style (hard)
- Follow `docs/CODING_STYLE.md`.
- Prefer explicit, readable code and long descriptive names.
- Comments are allowed to be verbose when they teach.

## Output style
- When writing CLI tools, prefer structured, human-readable output:
  - clear headings, tables, colored status messages
  - progress indicators for long operations
  - friendly, high-signal logs

## IPMI safety (hard)
- Never set fan speed below 0x09 (minimum idle).
- Always enforce 100% fan speed at DANGER_TEMP (80°C).
- Fan commands: `ipmitool raw 0x30 0x70 0x66 0x01 <zone> <speed>`
