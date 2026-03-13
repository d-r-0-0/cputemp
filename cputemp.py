"""cputemp — CPU temperature monitor and IPMI fan speed controller.

Displays a live Rich terminal dashboard showing CPU temperatures and
fan zone speeds for Supermicro servers, with automatic fan control
based on temperature thresholds.
"""
from __future__ import annotations

import glob
import os
import subprocess
import threading
import time

from rich.console import Console
from rich.live import Live
from rich.table import Table

# ---------------------------------------------------------------------------
# Configuration — tweak these to match your hardware and preferences.
# ---------------------------------------------------------------------------

# Temperature (°C) above which fans are forced to 100%.
DANGER_TEMPERATURE_CELSIUS = 80

# Maximum temperature used for scaling the display bars (not a real limit).
MAX_DISPLAY_TEMPERATURE = 100

# How long (seconds) a manual fan speed override stays active before
# automatic control resumes.
MANUAL_OVERRIDE_TIMEOUT_SECONDS = 10

# Default idle fan speed sent via IPMI when the CPU is cool.
# 0x09 is the lowest safe speed for our Supermicro board.
DEFAULT_IDLE_FAN_SPEED_HEX = 0x09

# Pre-computed percentage so we don't recalculate every loop iteration.
# 0x66 (102 decimal) is the IPMI maximum fan speed value.
DEFAULT_IDLE_FAN_SPEED_PERCENT = int((DEFAULT_IDLE_FAN_SPEED_HEX / 0x66) * 100)

# Below this average temperature, we use the default idle fan speed
# instead of the linear ramp.
IDLE_TEMPERATURE_THRESHOLD_CELSIUS = 55

# ---------------------------------------------------------------------------
# Global state for manual override (shared between the input thread and
# the main display loop).
# ---------------------------------------------------------------------------
last_manual_override_timestamp = 0
manual_override_speed_percent = None

def set_fan_speed_for_zones(speed_percent: int, zone: int | None = None) -> bool:
    """Send an IPMI raw command to set the fan PWM duty cycle.

    Maps a 0–100 percentage to the IPMI hex range 0x09 (idle) → 0x66 (max).
    If *zone* is None, both zones (0 and 1) are set.

    Returns True if all zone commands succeeded, False otherwise.
    """
    speed_percent = max(0, min(100, speed_percent))

    # Linear interpolation: 0% → 0x09, 100% → 0x66.
    ipmi_hex_value = int(
        DEFAULT_IDLE_FAN_SPEED_HEX
        + (speed_percent / 100.0) * (0x66 - DEFAULT_IDLE_FAN_SPEED_HEX)
    )
    formatted_hex_speed = format(ipmi_hex_value, '02x')

    target_zones = [0, 1] if zone is None else [zone]
    all_zones_succeeded = True

    for current_zone in target_zones:
        # Supermicro IPMI fan speed command format:
        #   ipmitool raw 0x30 0x70 0x66 0x01 <zone> <speed>
        ipmi_command = [
            "ipmitool", "raw",
            "0x30", "0x70", "0x66", "0x01",
            format(current_zone, '02x'),
            formatted_hex_speed,
        ]
        try:
            subprocess.run(
                ipmi_command,
                capture_output=True, text=True, check=True,
            )
        except subprocess.CalledProcessError as err:
            # Log but continue — one zone failing shouldn't block the other.
            print(f"Error setting fan zone {current_zone} speed: {err}")
            all_zones_succeeded = False

    return all_zones_succeeded

def read_current_fan_speeds() -> dict[str, float]:
    """Query IPMI for the current fan speed of each zone.

    Sends: ipmitool raw 0x30 0x70 0x66 0x00 <zone>
    The response is a single hex byte (e.g. " 1e\\n").  We parse it,
    convert to a 0–100% scale based on the 0x66 maximum, and return
    a dict like {"FAN Zone 0": 29.4, "FAN Zone 1": 29.4}.
    """
    fan_speed_percentages: dict[str, float] = {}

    for zone_index in [0, 1]:
        ipmi_command = [
            "ipmitool", "raw",
            "0x30", "0x70", "0x66", "0x00",
            f"0x0{zone_index}",
        ]
        try:
            result = subprocess.run(
                ipmi_command,
                capture_output=True, text=True, check=True,
            )
            # Response is a hex string like " 1e".  Strip whitespace,
            # parse as base-16 integer.
            raw_hex_value = int(result.stdout.strip(), 16)
            speed_as_percent = (raw_hex_value / 0x66) * 100
            speed_as_percent = max(0.0, min(100.0, speed_as_percent))
            fan_speed_percentages[f"FAN Zone {zone_index}"] = speed_as_percent
        except (subprocess.CalledProcessError, ValueError) as err:
            # If we can't read a zone, report 0% rather than crashing.
            print(f"Error reading fan speed for zone {zone_index}: {err}")
            fan_speed_percentages[f"FAN Zone {zone_index}"] = 0.0

    return fan_speed_percentages

def adjust_fan_speed_from_temperatures(
    temperature_readings: dict[str, float],
) -> bool:
    """Decide the correct fan speed and apply it.

    Decision priority (highest first):
      1. Manual override — if recently set by the user, honour it.
      2. Danger threshold — if ANY sensor >= DANGER_TEMPERATURE_CELSIUS,
         force 100%.
      3. Idle threshold — if the average temp is below
         IDLE_TEMPERATURE_THRESHOLD_CELSIUS, use the default idle speed.
      4. Linear ramp — interpolate between 30°C (0%) and
         DANGER_TEMPERATURE_CELSIUS (100%).
    """
    global last_manual_override_timestamp, manual_override_speed_percent

    # --- Priority 1: Manual override ---
    is_manual_override_active = (
        manual_override_speed_percent is not None
        and (time.time() - last_manual_override_timestamp)
        < MANUAL_OVERRIDE_TIMEOUT_SECONDS
    )
    if is_manual_override_active:
        return set_fan_speed_for_zones(manual_override_speed_percent)

    # --- Priority 2: Danger threshold ---
    is_any_sensor_dangerously_hot = any(
        temp >= DANGER_TEMPERATURE_CELSIUS
        for temp in temperature_readings.values()
    )
    if is_any_sensor_dangerously_hot:
        return set_fan_speed_for_zones(100)

    # --- Priority 3 & 4: Idle or linear ramp ---
    average_temperature = (
        sum(temperature_readings.values()) / len(temperature_readings)
    )

    if average_temperature < IDLE_TEMPERATURE_THRESHOLD_CELSIUS:
        return set_fan_speed_for_zones(DEFAULT_IDLE_FAN_SPEED_PERCENT)

    # Linear interpolation: 30°C → 0%, DANGER_TEMPERATURE_CELSIUS → 100%.
    if average_temperature <= 30:
        computed_speed_percent = 0
    elif average_temperature >= DANGER_TEMPERATURE_CELSIUS:
        computed_speed_percent = 100
    else:
        computed_speed_percent = int(
            (average_temperature - 30)
            / (DANGER_TEMPERATURE_CELSIUS - 30)
            * 100
        )

    return set_fan_speed_for_zones(computed_speed_percent)

def read_cpu_temperatures() -> dict[str, float]:
    """Read CPU temperatures from the Linux hwmon sysfs interface.

    Walks /sys/class/hwmon/hwmon*/temp*_input files, reads the
    millidegree value, and converts to °C.  If a corresponding
    *_label file exists (e.g. "Package id 0"), that label is used
    as the dict key; otherwise falls back to "CPU0", "CPU1", etc.

    Raises RuntimeError if no temperature sensors are found.
    """
    temperature_readings: dict[str, float] = {}
    sensor_count = 0

    for hwmon_directory in glob.glob('/sys/class/hwmon/hwmon*'):
        for directory_entry in os.scandir(hwmon_directory):
            is_temperature_input_file = (
                directory_entry.name.startswith('temp')
                and directory_entry.name.endswith('_input')
            )
            if not is_temperature_input_file:
                continue

            try:
                with open(directory_entry.path, 'r') as sensor_file:
                    millidegree_value = int(sensor_file.read().strip())
                    temperature_celsius = millidegree_value / 1000.0

                # Try to read the human-friendly label (e.g. "Package id 0").
                label_file_path = os.path.join(
                    hwmon_directory,
                    directory_entry.name[:-6] + '_label',
                )
                try:
                    with open(label_file_path, 'r') as label_file:
                        sensor_label = label_file.read().strip()
                except FileNotFoundError:
                    sensor_label = f"CPU{sensor_count}"

                temperature_readings[sensor_label] = temperature_celsius
                sensor_count += 1
            except Exception as read_error:
                print(f"Error reading {directory_entry.path}: {read_error}")

    if not temperature_readings:
        raise RuntimeError("No CPU temperature sensors found.")

    return temperature_readings

def get_temperature_bar_color(temperature: float) -> str:
    """Return a Rich color name based on how hot the sensor is.

    Green  = comfortable (< 60°C)
    Yellow = warm, starting to ramp fans (60–79°C)
    Red    = danger zone (≥ 80°C)
    """
    if temperature < 60:
        return "green"
    elif temperature < 80:
        return "yellow"
    else:
        return "red"


def render_temperature_bar(
    value: float,
    bar_width: int,
    show_value: bool = False,
    is_fan_speed: bool = False,
) -> str:
    """Build a Rich-formatted bar string for the dashboard.

    The bar is filled proportionally based on MAX_DISPLAY_TEMPERATURE
    and colored according to get_temperature_bar_color().  When
    *show_value* is True, the numeric reading is embedded in the bar.
    """
    if show_value:
        suffix = '%' if is_fan_speed else '°C'
        embedded_value_text = f" {value:.0f}{suffix} "
        text_length = len(embedded_value_text)
        remaining_bar_width = bar_width - text_length
        filled_block_count = int(
            remaining_bar_width * value / MAX_DISPLAY_TEMPERATURE
        )
        bar_string = (
            "█" * filled_block_count
            + embedded_value_text
            + " " * (remaining_bar_width - filled_block_count)
        )
    else:
        filled_block_count = int(bar_width * value / MAX_DISPLAY_TEMPERATURE)
        bar_string = (
            "█" * filled_block_count
            + " " * (bar_width - filled_block_count)
        )

    color = get_temperature_bar_color(value)
    return f"[{color}]{bar_string}[/{color}]"

def generate_dashboard_table(console_width: int) -> Table:
    """Build a Rich Table showing CPU temps and fan speeds.

    Reads temperatures, adjusts fans, reads fan speeds, and assembles
    everything into a single table for the Live display.
    """
    temperature_readings = read_cpu_temperatures()
    average_temperature = (
        sum(temperature_readings.values()) / len(temperature_readings)
    )

    table = Table(
        title="CPU Temperature & Fan Speed Monitor",
        expand=True,
    )
    table.add_column("Sensor", justify="left", no_wrap=True)
    table.add_column("Value", justify="center", no_wrap=True)
    table.add_column(
        f"Current Average Temp: {average_temperature:.1f}°C",
        justify="left",
        no_wrap=True,
    )

    bar_width = max(10, console_width - 30)

    if manual_override_speed_percent is not None:
        table.title = "CPU Temperature & Fan Speed Monitor (Manual Override)"

    # Apply fan speed based on current temperature readings.
    adjust_fan_speed_from_temperatures(temperature_readings)

    # --- CPU temperature rows ---
    for sensor_label, temperature in temperature_readings.items():
        table.add_row(
            sensor_label,
            f"{temperature:.1f}°C",
            render_temperature_bar(temperature, bar_width, show_value=True),
        )

    # --- Separator ---
    table.add_row("", "", "")

    # --- Fan speed rows ---
    fan_speed_readings = read_current_fan_speeds()
    for fan_label, speed_percent in fan_speed_readings.items():
        table.add_row(
            fan_label,
            f"{speed_percent:.0f}%",
            render_temperature_bar(
                speed_percent, bar_width,
                show_value=True, is_fan_speed=True,
            ),
        )

    return table

def handle_user_fan_speed_input() -> None:
    """Blocking prompt for manual fan speed override.

    Accepts:
      - A number 0–100 to set manual fan speed (both zones).
      - 'a' to return to automatic mode.
    """
    global manual_override_speed_percent, last_manual_override_timestamp
    try:
        user_input = input(
            "Enter fan speed (0-100, or 'a' for auto): "
        )
        if user_input.lower() == 'a':
            manual_override_speed_percent = None
            print("Automatic fan control enabled.")
        else:
            requested_speed = int(user_input)
            if 0 <= requested_speed <= 100:
                manual_override_speed_percent = requested_speed
                last_manual_override_timestamp = time.time()
                print(
                    f"Manual override: fan speed → "
                    f"{manual_override_speed_percent}%"
                )
            else:
                print("Invalid: enter 0–100, or 'a'.")
    except ValueError:
        print("Invalid: enter a number or 'a'.")
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass


def run_input_loop_forever() -> None:
    """Continuously prompt for user input (runs in a daemon thread)."""
    while True:
        handle_user_fan_speed_input()
        time.sleep(0.1)


def set_initial_idle_fan_speed() -> None:
    """Set fans to the default idle speed on startup."""
    print(
        f"Setting initial fan speed to "
        f"{DEFAULT_IDLE_FAN_SPEED_PERCENT}% "
        f"(hex: {DEFAULT_IDLE_FAN_SPEED_HEX:02x})"
    )
    set_fan_speed_for_zones(DEFAULT_IDLE_FAN_SPEED_PERCENT)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    console = Console()
    previous_rendered_table = None

    try:
        set_initial_idle_fan_speed()

        # The input prompt blocks, so it runs in a background daemon thread
        # while the Rich Live display updates in the main thread.
        input_thread = threading.Thread(
            target=run_input_loop_forever, daemon=True,
        )
        input_thread.start()

        console_width = console.width

        with Live(
            generate_dashboard_table(console_width),
            refresh_per_second=1,
            console=console,
            screen=True,
        ) as live_display:
            while True:
                current_table = generate_dashboard_table(console_width)
                current_table_string = str(current_table)

                # Only push an update when the table content has changed,
                # to avoid unnecessary redraws.
                if current_table_string != previous_rendered_table:
                    live_display.update(current_table)
                    previous_rendered_table = current_table_string

                time.sleep(1)

    except RuntimeError as runtime_error:
        print(runtime_error)
    except KeyboardInterrupt:
        print("\nShutting down — returning fans to idle speed.")
        set_fan_speed_for_zones(DEFAULT_IDLE_FAN_SPEED_PERCENT)