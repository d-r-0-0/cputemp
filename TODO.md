# cputemp — Feature Slice Backlog

> Each slice is designed to be handed to an agent (or a human) as an
> independent unit of work using the templates in `.github/AGENT_PROMPTS.md`.

---

## 🧹 CLEANUP — Technical Debt & Housekeeping

### CLEAN-1: Extract fan control into separate module

- **Template:** REFACTOR
- **Effort:** Medium
- **Files:** `cputemp.py`, `fan_control.py` (new)
- **What:**
  - Move `set_fan_speed`, `get_fan_speeds`, `adjust_fan_speed` into
    a dedicated `fan_control.py` module.
  - Import into `cputemp.py`.
- **Acceptance:**
  - Same behavior, cleaner separation.
  - `make verify` passes.

### CLEAN-2: Extract temperature reading into separate module

- **Template:** REFACTOR
- **Effort:** Small
- **Files:** `cputemp.py`, `temperature.py` (new)
- **What:**
  - Move `get_cpu_temps` and related hwmon logic into `temperature.py`.
- **Acceptance:**
  - Same behavior.
  - `make verify` passes.

---

## 🧪 TESTING — Coverage Expansion

### TEST-1: Unit tests for fan speed mapping

- **Template:** FEATURE SLICE
- **Effort:** Small
- **Files:** `tests/test_fan_control.py` (new)
- **What:**
  - Test `set_fan_speed` hex mapping (0→0x09, 100→0x66).
  - Test `get_fan_speeds` parsing of hex output.
  - Mock all subprocess calls.
- **Acceptance:**
  - ≥ 5 new tests, all passing.

### TEST-2: Unit tests for temperature thresholds

- **Template:** FEATURE SLICE
- **Effort:** Small
- **Files:** `tests/test_temperature.py` (new)
- **What:**
  - Test `adjust_fan_speed` at boundary temps (30, 55, 80, 100).
  - Test manual override logic.
  - Mock subprocess and hwmon reads.
- **Acceptance:**
  - ≥ 5 new tests, all passing.

---

## ✨ FEATURES — New Functionality

### FEAT-1: Per-zone manual fan speed override

- **Template:** FEATURE SLICE
- **Effort:** Small
- **Files:** `cputemp.py`
- **What:**
  - Allow input like `0:50` to set zone 0 to 50%, leaving zone 1
    on auto.
- **Acceptance:**
  - Per-zone override works via keyboard input.
  - `make verify` passes.

### FEAT-2: Configuration file support

- **Template:** FEATURE SLICE
- **Effort:** Medium
- **Files:** `cputemp.py`, `config.py` (new), `cputemp.conf` (new)
- **What:**
  - Move hardcoded constants to a config file.
  - Support TOML or INI format.
- **Acceptance:**
  - Config file is read at startup.
  - Fallback to defaults if file missing.
  - `make verify` passes.

---

## 📋 DONE — Completed Slices

### Bootstrap
- [x] Initial project setup
- [x] Live Rich dashboard with temperature bars
- [x] IPMI fan control integration
- [x] systemd + tmux service
- [x] Template compliance (AGENTS.md, CLAUDE.md, etc.)
