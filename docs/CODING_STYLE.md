# Coding Style

## Clean Code defaults
- Functions should do one thing.
- Small functions; avoid deep nesting.
- Clear naming; prefer intention-revealing names.
- Keep modules cohesive; separate responsibilities.
- Prefer refactoring into simpler structures over cleverness.

## Naming
- Prefer long, descriptive variable and function names.
- Boolean names should read naturally
  (`is_temperature_above_danger_threshold`, `has_valid_fan_reading`).

## Comments
- Comments should teach intent and reasoning:
  - "why" > "what"
- Verbose comments are acceptable when used as instruction or
  explanation for future readers (human or AI).
- If behavior is subtle, include an example in a comment.

## Command line & automation (non-negotiable)
- No CLI command > 80 characters.
- If it would be longer:
  - write a cantrip in `cantrips/`
  - add a short alias in `Makefile`

## "Cantrip" standard
Every cantrip starts with a header block that includes:
- **Purpose** — what it does and why it exists
- **Usage** — example invocations
- **Dependencies** — runtime requirements
- **Functions** — one-line explanation of each function

## Output style
- Prefer structured CLI output:
  - headings, tables, panels
  - colored status messages
  - progress indicators for long operations
- Keep logs readable and consistent.

## Python specifics
- Type annotations on all public functions.
- Use `from __future__ import annotations` at top of modules.
- Exception re-raises must use `from err` or `from None`.
- Imports sorted: stdlib, third-party, local (isort order).
- Use `subprocess.run()` over `subprocess.call()` / `check_output()`.
