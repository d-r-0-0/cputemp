# cputemp — CPU Temperature Monitor & IPMI Fan Controller

> CPU temperature monitor and IPMI fan speed controller for Supermicro
> servers.  Displays a live Rich terminal dashboard showing CPU
> temperatures and fan zone speeds, with automatic fan control based
> on temperature thresholds.

---

## Features

- Real-time CPU temperature monitoring via `/sys/class/hwmon`
- Automatic IPMI fan speed control (two zones) using `ipmitool`
- Live terminal dashboard with color-coded temperature bars
- Manual fan speed override via keyboard input
- Runs as a systemd service inside a tmux session for persistence

## Requirements

- Python 3.11+
- `ipmitool` (for fan control)
- `tmux` (for persistent session)
- Supermicro IPMI-compatible motherboard

## Installation

```bash
# Clone the repo
git clone https://github.com/d-r-0-0/cputemp.git /opt/cputemp
cd /opt/cputemp

# Create virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Install dev tools (linting, testing)
make install-dev

# Install the systemd service
sudo cp systemd/cputemp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cputemp
sudo systemctl start cputemp
```

## Usage

### Attach to the live display

```bash
tmux attach -t cputemp
```

Once attached, type a fan speed (0-100) or `a` for automatic mode.
Detach with `Ctrl+B` then `D`.

### Service management

```bash
systemctl status cputemp    # Check status
systemctl restart cputemp   # Restart
systemctl stop cputemp      # Stop
journalctl -u cputemp       # View logs
```

### Development

```bash
make verify    # Run lint + tests
make lint      # Lint only (ruff)
make fmt       # Format (ruff format)
make test      # Tests only (pytest)
```

## Configuration

Edit the constants at the top of `cputemp.py`:

| Variable | Default | Description |
|---|---|---|
| `DANGER_TEMP` | 80 | Temperature (°C) that triggers 100% fan speed |
| `MAX_TEMP` | 100 | Maximum temperature for display scaling |
| `MANUAL_OVERRIDE_TIMEOUT` | 10 | Seconds manual override stays active |
| `DEFAULT_FAN_SPEED_HEX` | 0x09 | Default idle fan speed (IPMI hex value) |
| `TEMP_THRESHOLD` | 55 | Below this temp, use default idle speed |

## IPMI Commands

This tool uses the following IPMI raw commands (Supermicro format):

- **Set fan speed:** `ipmitool raw 0x30 0x70 0x66 0x01 <zone> <speed>`
- **Read fan speed:** `ipmitool raw 0x30 0x70 0x66 0x00 <zone>`

Where `<zone>` is `0x00` or `0x01` and `<speed>` ranges from `0x09`
to `0x66`.

## File Layout

```
cputemp.py             # Main script — monitor + fan control
requirements.txt       # Python dependencies
systemd/
  cputemp.service      # systemd unit file (source of truth)
cantrips/              # Automation scripts
docs/                  # Documentation
sessions/              # Session close-out logs
AGENTS.md              # Universal AI agent instructions
CLAUDE.md              # Claude Code instructions
TODO.md                # Feature backlog
```

## License

MIT
