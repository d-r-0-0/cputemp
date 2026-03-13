"""Placeholder test to verify pytest runs correctly."""
from __future__ import annotations


def test_configuration_constants_are_sane():
    """Verify that the hardcoded configuration values are within
    reasonable ranges — a basic smoke test."""
    # Import here so the test can run even without ipmitool installed.
    import importlib
    cputemp = importlib.import_module("cputemp")

    assert 50 <= cputemp.DANGER_TEMPERATURE_CELSIUS <= 105
    assert cputemp.MAX_DISPLAY_TEMPERATURE >= cputemp.DANGER_TEMPERATURE_CELSIUS
    assert 0 < cputemp.DEFAULT_IDLE_FAN_SPEED_HEX <= 0x66
    assert 0 <= cputemp.DEFAULT_IDLE_FAN_SPEED_PERCENT <= 100
    assert cputemp.MANUAL_OVERRIDE_TIMEOUT_SECONDS > 0
