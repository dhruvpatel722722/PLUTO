"""Alert generation based on dwell time thresholds."""
from datetime import datetime


class AlertGenerator:
    """Generates alerts when assets exceed dwell thresholds in zones."""

    def __init__(self, config):
        self._config = config
        self._threshold = config.dwell_threshold
        self._max_alerts = config.max_alerts

    def generate_alerts(self, dwell_times, events):
        """Produce alert records for assets exceeding dwell threshold.

        Args:
            dwell_times: dict of {(asset_id, zone_id): seconds}
            events: sorted event list for timestamp lookups

        Returns:
            List of alert dicts
        """
        alerts = []
        asset_last_seen = {}

        for event in events:
            if event["zone_id"] is not None:
                key = (event["asset_id"], event["zone_id"])
                asset_last_seen[key] = event["timestamp"]

        for (asset_id, zone_id), duration in dwell_times.items():
            if duration >= self._threshold:
                last_ts = asset_last_seen.get((asset_id, zone_id))
                alert = {
                    "alert_type": "dwell_exceeded",
                    "asset_id": asset_id,
                    "zone_id": zone_id,
                    "dwell_seconds": round(duration, 1),
                    "threshold_seconds": self._threshold,
                    "last_seen": last_ts.isoformat() if last_ts else None,
                    "severity": self._compute_severity(duration),
                }
                alerts.append(alert)

                if len(alerts) >= self._max_alerts:
                    break

        return alerts

    def _compute_severity(self, duration):
        """Determine alert severity based on overage amount."""
        overage = duration - self._threshold
        if overage >= self._threshold:
            return "critical"
        elif overage >= self._threshold * 0.5:
            return "high"
        else:
            return "medium"
