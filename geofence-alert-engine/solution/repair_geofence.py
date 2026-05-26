#!/usr/bin/env python3
"""Repair script for the geofence alert engine.

Patches four defects in the runtime source files and re-runs the engine.
"""
import os
import sys


def patch_config_loader():
    """Fix Bug A: strip whitespace from comma-separated active_feeds.
    Fix Bug B: read dwell_threshold from alerting.realtime section.
    """
    path = "/app/runtime/config_loader.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug A: feeds are not stripped after split, so " beacon_west" never matches
    content = content.replace(
        'self._active_feeds = set(raw_feeds.split(","))',
        'self._active_feeds = set(item.strip() for item in raw_feeds.split(","))'
    )

    # Bug B: reads from [alerting] instead of [alerting.realtime]
    content = content.replace(
        'self._dwell_threshold = self._parser.getint("alerting", "dwell_threshold_sec")',
        'self._dwell_threshold = self._parser.getint("alerting.realtime", "dwell_threshold_sec")'
    )
    content = content.replace(
        'self._cooldown = self._parser.getint("alerting", "cooldown_sec")',
        'self._cooldown = self._parser.getint("alerting.realtime", "cooldown_sec")'
    )
    content = content.replace(
        'self._max_alerts = self._parser.getint("alerting", "max_alerts_per_window")',
        'self._max_alerts = self._parser.getint("alerting.realtime", "max_alerts_per_window")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_event_ingestor():
    """Fix Bug D: add sensor_id to sort key for deterministic ordering."""
    path = "/app/runtime/event_ingestor.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug D: sort key missing sensor_id, causes non-deterministic order for same-timestamp events
    content = content.replace(
        'all_events.sort(key=lambda e: (e["timestamp"], e["seq"]))',
        'all_events.sort(key=lambda e: (e["timestamp"], e["sensor_id"], e["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_dwell_tracker():
    """Fix Bug C: use last-write-wins instead of accumulating across windows."""
    path = "/app/runtime/dwell_tracker.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug C: accumulates dwell across windows instead of using final window value
    content = content.replace(
        '            for key, duration in window_dwell.items():\n                dwell_totals[key] += duration',
        '            for key, duration in window_dwell.items():\n                dwell_totals[key] = duration'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_config_loader()
    patch_event_ingestor()
    patch_dwell_tracker()

    # Re-run engine with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_engine import main as run_main
    run_main()


if __name__ == "__main__":
    main()
