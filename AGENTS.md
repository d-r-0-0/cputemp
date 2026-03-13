# AGENTS.md — Instructions for All AI Coding Agents

> **Audience:** Codex, Claude Code, Jules, Copilot, and any other AI
> agent that works on this repo.  Read this file in full before
> writing any code.

---

## 1. Mandatory Reading (before any work)

| File | What it covers |
|------|---------------|
| `.github/copilot-instructions.md` | Operating mode, command-line rule, verification loop |
| `docs/CODING_STYLE.md` | Naming, comments, output conventions, cantrip standard |
| `sessions/` + `.github/AI_LESSONS.md` | Session history and curated lessons from past work |

---

## 2. Project Overview

CPU temperature monitor and IPMI fan speed controller for Supermicro
servers.  Displays a live Rich terminal dashboard showing CPU
temperatures and fan zone speeds, with automatic fan control based
on temperature thresholds.

**Stack:** Python 3.11, Rich (terminal UI), ipmitool (IPMI fan control), systemd + tmux (service management)

---

## 3. Hard Rules (non-negotiable)

### 3.1 Command-line rule
- **No CLI command > 80 characters.**
- If a command would exceed 80 chars, create a cantrip in `cantrips/`.

### 3.2 Verification loop
- **Every time you claim "done", run `make verify`**
  (or `./cantrips/verify.sh` on systems without Make).
- If it fails, fix and rerun.  Max 5 iterations.  If still failing,
  stop and report what's broken.

### 3.3 Coding style
- Follow `docs/CODING_STYLE.md` strictly.
- **Long descriptive names.**  Verbose teaching comments are welcome.
- **Small diffs** — prefer < 300 lines per commit.  Split larger work
  into sub-slices with one commit each.

### 3.4 Exception handling
- All re-raises inside `except` blocks **must** preserve the chain.
  Use `from err` or `from None` — no bare re-raises that lose context.

### 3.5 No behavior changes in refactors
- REFACTOR tasks must preserve identical user-facing behavior.
- Same outputs, same API contracts, same test results.

### 3.6 Session close-out (human responsibility)

At the end of each coding block (when you're about to step away),
run `make closeout` to capture what happened.

### 3.7 IPMI safety
- **Never** set fan speed to 0x00 — always use 0x09 as the
  minimum idle speed.
- **Always** enforce 100% fan speed when any CPU exceeds
  DANGER_TEMP (80°C).
- Fan speed commands use the Supermicro format:
  `ipmitool raw 0x30 0x70 0x66 0x01 <zone> <speed>`

---

## 4. Key Commands

```bash
make verify       # lint + test (PRIMARY — use this)
make lint         # lint only (ruff)
make fmt          # format only (ruff format)
make test         # test only (pytest)
```

---

## 5. File Layout

```
cputemp.py             # Main script — monitor + fan control
requirements.txt       # Python dependencies
systemd/
  cputemp.service      # systemd unit file (source of truth)
cantrips/              # Automation scripts
docs/                  # Documentation
sessions/              # Session close-out logs (institutional memory)
```

---

## 6. Delivery Rules

### 6.1 Standard delivery (GitHub-comment agents: Codex, Jules)
1. Push your branch to origin.
2. Open a Pull Request with a clear title and summary.
3. **Actually make the code changes** — do NOT just describe what
   you would do.

### 6.2 Cloud / sandbox delivery (Claude Code Cloud, etc.)
If your environment uses a git proxy (remote URL contains
`127.0.0.1` or `local_proxy`), you **cannot** open PRs:

1. **Actually make the code changes** — do NOT just describe.
2. Push your branch: `git push -u origin <branch-name>`
3. **STOP after pushing.**  Do NOT attempt to open a PR.

---

## 7. Bailout Rules (prevents wasted tokens)

- If any step fails **twice** with the same error, **STOP immediately.**
- If you hit a rate limit, usage cap, or auth error, **STOP.**
- Do NOT retry failed commands more than twice.
- **Priority order:** code quality > passing tests > push > PR.
- When stopping early, print a clear summary:
  1. What completed successfully
  2. What failed and why
  3. What remains to be done

---

## 8. Testing Guidance

- **Mock all external services** — ipmitool calls, hwmon reads.
  No real hardware calls in tests.
- Use pytest with fixtures.

---

## 9. Commit Messages

Use conventional commits:

```
refactor: extract fan control into separate module
feat: add per-zone fan speed override
fix: handle hex parsing for fan speed readings
test: add temperature threshold edge case tests
```

One commit per logical slice.  Each commit must pass `make verify`.

---

## 10. Review Tasks (Jules / verification agents)

When assigned a **review** task:
- Your job is to **REVIEW and REPORT**.  Do NOT write code.
- Run the verification checklist from section 3 above.
- Report ✅ / ❌ per item with file + line references.
- Recommend: APPROVE or REQUEST CHANGES.
