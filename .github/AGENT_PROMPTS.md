# Agent Prompt Templates

> Copy-paste these into GitHub issues or agent prompts.
> Fill in the `{{...}}` placeholders before dispatching.

---

## FEATURE SLICE

```
You are working on the `cputemp` project — a CPU temperature monitor
and IPMI fan controller for Supermicro servers.

Read `AGENTS.md` and `docs/CODING_STYLE.md` before starting.

**Task:** {{DESCRIPTION}}

**Files to create/modify:** {{FILES}}

**Acceptance criteria:**
- {{CRITERIA}}
- `make verify` passes

**Branch name:** `feat/{{SHORT_NAME}}`
```

---

## CI FIX

```
You are working on the `cputemp` project.

Read `AGENTS.md` before starting.

**Task:** CI is failing. Diagnose and fix.

1. Run `make verify` and observe the failure.
2. Fix the root cause (not just symptoms).
3. Rerun `make verify` — must pass.
4. Commit with message: `fix: {{DESCRIPTION}}`
```

---

## REFACTOR

```
You are working on the `cputemp` project.

Read `AGENTS.md` and `docs/CODING_STYLE.md` before starting.

**Task:** {{DESCRIPTION}}

**Constraint:** This is a REFACTOR.  User-facing behavior must be
identical before and after.  Same outputs, same fan control behavior.

**Files:** {{FILES}}

**Branch name:** `refactor/{{SHORT_NAME}}`
```
