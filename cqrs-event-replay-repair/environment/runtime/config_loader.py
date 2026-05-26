"""Configuration loader for the event replay engine."""
import configparser
import os


class ReplayConfig:
    """Loads and provides access to replay engine configuration."""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "settings.ini"
            )
        self._config = configparser.ConfigParser()
        self._config.read(config_path)

    @property
    def data_directory(self):
        return self._config.get("sources", "data_directory")

    @property
    def output_directory(self):
        return self._config.get("sources", "output_directory")

    @property
    def accepted_event_types(self):
        """Return set of event types that should be processed."""
        raw = self._config.get("sources", "accepted_event_types")
        return set(raw.split(","))

    @property
    def batch_size(self):
        """Number of events to process per projection batch."""
        return self._config.getint("replay", "batch_size")

    @property
    def snapshot_interval(self):
        return self._config.getint("replay.projection", "snapshot_interval")

    @property
    def output_projections_file(self):
        return self._config.get("output", "projections_file")

    @property
    def output_summary_file(self):
        return self._config.get("output", "summary_file")
