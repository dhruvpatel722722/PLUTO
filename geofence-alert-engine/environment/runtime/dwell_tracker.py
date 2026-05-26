"""Dwell time tracking for assets within geofence zones."""
from collections import defaultdict
from datetime import timedelta


class DwellTracker:
    """Tracks how long assets remain within each zone across time windows."""

    def __init__(self, config):
        self._config = config
        self._window_sec = config.time_window
        self._batch_size = config.batch_size

    def compute_dwell_times(self, events):
        """Compute per-asset dwell times in each zone using time windows.

        Returns dict: {(asset_id, zone_id): total_dwell_seconds}
        """
        if not events:
            return {}

        # Group events into time windows
        windows = self._partition_windows(events)

        # Track dwell across windows
        dwell_totals = defaultdict(float)

        for window_events in windows:
            window_dwell = self._compute_window_dwell(window_events)
            for key, duration in window_dwell.items():
                dwell_totals[key] += duration

        return dict(dwell_totals)

    def _partition_windows(self, events):
        """Split events into fixed time windows."""
        if not events:
            return []

        windows = []
        current_window = []
        window_start = events[0]["timestamp"]

        for event in events:
            elapsed = (event["timestamp"] - window_start).total_seconds()
            if elapsed >= self._window_sec:
                if current_window:
                    windows.append(current_window)
                current_window = [event]
                window_start = event["timestamp"]
            else:
                current_window.append(event)

        if current_window:
            windows.append(current_window)

        return windows

    def _compute_window_dwell(self, window_events):
        """Compute dwell times within a single time window."""
        asset_zone_times = defaultdict(list)

        for event in window_events:
            if event["zone_id"] is not None:
                key = (event["asset_id"], event["zone_id"])
                asset_zone_times[key].append(event["timestamp"])

        dwell = {}
        for key, timestamps in asset_zone_times.items():
            if len(timestamps) >= 2:
                duration = (timestamps[-1] - timestamps[0]).total_seconds()
                dwell[key] = duration
            else:
                dwell[key] = 0.0

        return dwell
