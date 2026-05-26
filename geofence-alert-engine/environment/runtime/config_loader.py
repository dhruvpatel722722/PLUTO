"""Configuration loader for the geofence alert engine."""
import configparser
import os


class ConfigLoader:
    """Loads and provides access to engine configuration."""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "settings.ini"
            )
        self._parser = configparser.ConfigParser()
        self._parser.read(config_path)
        self._load_settings()

    def _load_settings(self):
        """Parse all configuration sections."""
        # Load active sensor feeds
        raw_feeds = self._parser.get("sensors", "active_feeds")
        self._active_feeds = set(raw_feeds.split(","))

        # Load zone definitions
        self._zones = {}
        for key in self._parser.options("zones"):
            parts = self._parser.get("zones", key).split(":")
            self._zones[key] = {
                "lat_min": float(parts[0]),
                "lat_max": float(parts[1]),
                "lon_min": float(parts[2].replace("\u2212", "-")),
                "lon_max": float(parts[3].replace("\u2212", "-")),
            }

        # Load alerting thresholds
        # Uses general alerting section for threshold configuration
        self._dwell_threshold = self._parser.getint("alerting", "dwell_threshold_sec")
        self._cooldown = self._parser.getint("alerting", "cooldown_sec")
        self._max_alerts = self._parser.getint("alerting", "max_alerts_per_window")

        # Load processing params
        self._batch_size = self._parser.getint("processing", "batch_size")
        self._time_window = self._parser.getint("processing", "time_window_sec")
        self._dedup_window = self._parser.getint("processing", "dedup_window_sec")

    @property
    def active_feeds(self):
        return self._active_feeds

    @property
    def zones(self):
        return self._zones

    @property
    def dwell_threshold(self):
        return self._dwell_threshold

    @property
    def cooldown(self):
        return self._cooldown

    @property
    def max_alerts(self):
        return self._max_alerts

    @property
    def batch_size(self):
        return self._batch_size

    @property
    def time_window(self):
        return self._time_window

    @property
    def dedup_window(self):
        return self._dedup_window
