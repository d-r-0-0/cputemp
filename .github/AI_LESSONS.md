# AI Lessons — Curated from Session Logs

> Distilled lessons from past coding sessions.  Read before starting work.

---

## IPMI Hex Formatting

- ipmitool requires `0x` prefix on hex values.  Bare hex like `09`
  causes "Given data is invalid" errors.  Always use `0x09`.

## Fan Speed Value Parsing

- Fan speed readings from `ipmitool raw 0x30 0x70 0x66 0x00 <zone>`
  return hex strings (e.g., " 1e").  Strip whitespace, parse with
  `int(value, 16)`.

## systemd + tmux

- tmux forks and the parent exits immediately.  Use `Type=forking`
  with `RemainAfterExit=yes` so systemd considers the service active.

## Threading + Rich Live

- The `input()` call blocks, so it must run in a daemon thread to
  avoid freezing the Rich Live display.
