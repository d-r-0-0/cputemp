from rich.console import Console
from rich.live import Live
from rich.table import Table
import time
import random
import glob
import os
import subprocess
import threading

# Configuration
DANGER_TEMP = 80
MAX_TEMP = 100
MANUAL_OVERRIDE_TIMEOUT = 10
DEFAULT_FAN_SPEED_HEX = 0x09  # Default fan speed (hex)
DEFAULT_FAN_SPEED_PCT = int((DEFAULT_FAN_SPEED_HEX / 0x66) * 100)  # Calculate percentage
TEMP_THRESHOLD = 55 # Temperature threshold for default fan speed

# Global variables
last_manual_override = 0
manual_speed = None

def set_fan_speed(speed_percent, zone=None):
    speed_percent = max(0, min(100, speed_percent))
    hex_speed = int(0x09 + (speed_percent / 100.0) * (0x66 - 0x09))
    hex_speed = format(hex_speed, '02x')

    zones = [0, 1] if zone is None else [zone]
    success = True

    for z in zones:
        cmd = ["ipmitool", "raw", "0x30", "0x70", "0x66", "0x01",
               format(z, '02x'), hex_speed]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error setting fan zone {z} speed: {e}")
            success = False
    return success

def get_fan_speeds():
    try:
        fan_speeds = {}
        for zone in [0, 1]:
            cmd = ["ipmitool", "raw", "0x30", "0x70", "0x66", "0x00", "0x0" + str(zone)]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                speed_val = int(result.stdout.strip(), 16)
                speed_pct = (speed_val / 0x66) * 100
                speed_pct = max(0, min(100, speed_pct))
                fan_speeds[f"FAN Zone {zone}"] = speed_pct
            except (subprocess.CalledProcessError, ValueError) as e:
                print(f"Error getting/converting speed for zone {zone}: {e}")
                fan_speeds[f"FAN Zone {zone}"] = 0
        return fan_speeds
    except Exception as e:
        print(f"Unexpected error in get_fan_speeds: {e}")
        return {"FAN Zone 0": 0, "FAN Zone 1": 0}

def adjust_fan_speed(temps):
    global last_manual_override, manual_speed

    if manual_speed is not None and (time.time() - last_manual_override) < MANUAL_OVERRIDE_TIMEOUT:
        return set_fan_speed(manual_speed)

    if any(temp >= DANGER_TEMP for temp in temps.values()):
        return set_fan_speed(100)

    avg_temp = sum(temps.values()) / len(temps)

    # Check if below threshold, and set default speed if so
    if avg_temp < TEMP_THRESHOLD:
        return set_fan_speed(DEFAULT_FAN_SPEED_PCT)  # Use the calculated percentage
    else:
        # Original scaling logic
        if avg_temp <= 30:
            speed = 0
        elif avg_temp >= DANGER_TEMP:
            speed = 100
        else:
            speed = int((avg_temp - 30) / (DANGER_TEMP - 30) * 100)
        return set_fan_speed(speed)

def get_cpu_temps():
    temps = {}
    cpu_count = 0
    try:
        for hwmon_dir in glob.glob('/sys/class/hwmon/hwmon*'):
            for entry in os.scandir(hwmon_dir):
                if entry.name.startswith('temp') and entry.name.endswith('_input'):
                    try:
                        with open(entry.path, 'r') as f:
                            temp_milli = int(f.read().strip())
                            temp_c = temp_milli / 1000.0
                        label_path = os.path.join(hwmon_dir, entry.name[:-6] + '_label')
                        try:
                            with open(label_path, 'r') as f:
                                label = f.read().strip()
                        except FileNotFoundError:
                            label = f"CPU{cpu_count}"
                        temps[label] = temp_c
                        cpu_count += 1
                    except Exception as e:
                        print(f"Error reading {entry.path}: {e}")
        if not temps:
            # Instead of falling back, raise an exception
            raise RuntimeError("No CPU temperature sensors found.")
        return temps
    except Exception as e:
        print(f"Error in get_cpu_temps: {e}")
        # Re-raise the exception to stop execution
        raise

def get_color(temp):
    if temp < 60:
        return "green"
    elif temp < 80:
        return "yellow"
    else:
        return "red"

def render_bar(temp, width, show_value=False, is_fan=False):
    filled_length = int(width * temp / MAX_TEMP)
    if show_value:
        value_text = f" {temp:.0f}{'%' if is_fan else '°C'} "
        text_length = len(value_text)
        remaining_width = width - text_length
        filled_length = int(remaining_width * temp / MAX_TEMP)
        bar = "█" * filled_length + value_text + " " * (remaining_width - filled_length)
    else:
        bar = "█" * filled_length + " " * (width - filled_length)
    color = get_color(temp)
    return f"[{color}]{bar}[/{color}]"

def generate_table(console_width):
    temps = get_cpu_temps()
    avg_temp = sum(temps.values()) / len(temps)

    table = Table(title="CPU Temperature & Fan Speed Monitor", expand=True)
    table.add_column("Sensor", justify="left", no_wrap=True)
    table.add_column("Value", justify="center", no_wrap=True)
    table.add_column(f"Current Average Temp: {avg_temp:.1f}°C", justify="left", no_wrap=True)

    bar_width = console_width - 30
    if bar_width < 10:
        bar_width = 10

    if manual_speed is not None:
        table.title = "CPU Temperature & Fan Speed Monitor (Manual Override)"
    else:
        table.title = "CPU Temperature & Fan Speed Monitor"

    adjust_fan_speed(temps)

    for cpu, temp in temps.items():
        table.add_row(cpu, f"{temp:.1f}°C", render_bar(temp, bar_width, show_value=True))

    table.add_row("", "", "")

    fan_speeds = get_fan_speeds()
    for fan, speed in fan_speeds.items():
        table.add_row(
            fan,
            f"{speed:.0f}%",
            render_bar(speed, bar_width, show_value=True, is_fan=True)
        )

    return table

def check_for_keypress():
    """Check for user input and set manual fan speed (BLOCKING)."""
    global manual_speed, last_manual_override
    try:
        user_input = input("Enter fan speed (0-100, or 'a' for auto): ")
        if user_input.lower() == 'a':
            manual_speed = None
            print("Automatic fan control enabled.")
        else:
            speed = int(user_input)
            if 0 <= speed <= 100:
                manual_speed = speed
                last_manual_override = time.time()
                print(f"Manual override: setting fan speed to {manual_speed}%")
            else:
                print("Invalid input. Please enter a number between 0 and 100, or 'a'.")
    except ValueError:
        print("Invalid input. Please enter a number or 'a'.")
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass

def input_loop():
    """Continuously check for user input in a separate thread."""
    while True:
        check_for_keypress()
        time.sleep(0.1)

def set_initial_fan_speed():
    """Sets the initial fan speed to the default value."""
    print(f"Setting initial fan speed to {DEFAULT_FAN_SPEED_PCT}% (hex: {DEFAULT_FAN_SPEED_HEX:02x})")
    set_fan_speed(DEFAULT_FAN_SPEED_PCT)

console = Console()
previous_table_data = None

# --- Main Program Start ---
try:
    set_initial_fan_speed()  # Set the initial fan speed

    # Start the input thread
    input_thread = threading.Thread(target=input_loop, daemon=True)
    input_thread.start()

    # Get the console width *before* entering the Live context
    console_width = console.width

    with Live(generate_table(console_width), refresh_per_second=1, console=console, screen=True) as live:
        while True:
            current_table = generate_table(console_width)
            current_table_data = str(current_table)

            if current_table_data != previous_table_data:
                live.update(current_table)
                previous_table_data = current_table_data

            time.sleep(1)
except RuntimeError as e:
    print(e) #Print error if we cannot find sensors.
except Exception as ex:
    print(ex)