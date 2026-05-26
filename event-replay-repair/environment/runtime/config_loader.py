"""Configuration loader for the event replay engine.

Reads settings from the INI configuration file and provides typed access
to all configuration parameters used by the replay stages.
"""
import configparser
import os


class ReplayConfig:
    """Loads and provides access to replay engine configuration.

    Configuration is organized into sections:
    - [sources]: Data input paths and format
    - [sources.filter]: Event type filtering rules
    - [replay]: General replay parameters
    - [replay.engine]: Engine-specific batch and snapshot settings
    - [output]: Output file configuration
    """

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "settings.ini"
            )
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._parse_filter_config()

    def _parse_filter_config(self):
        """Pre-parse filter configuration for efficient lookups."""
        raw_types = self._config.get("sources.filter", "accepted_types")
        self._accepted_types = set(raw_types.split(","))

    @property
    def data_directory(self):
        return self._config.get("sources", "data_directory")

    @property
    def output_directory(self):
        return self._config.get("sources", "output_directory")

    @property
    def accepted_event_types(self):
        """Return set of event types that pass the filter stage."""
        return self._accepted_types

    @property
    def batch_size(self):
        """Batch size for the projection replay engine."""
        return self._config.getint("replay", "batch_size")

    @property
    def snapshot_interval(self):
        """How often to emit intermediate snapshots."""
        return self._config.getint("replay.engine", "snapshot_interval")

    @property
    def accumulation_mode(self):
        """How batch results apply to projections: 'replace' or 'accumulate'."""
        return self._config.get("replay.engine", "accumulation_mode")

    @property
    def output_projections_file(self):
        return self._config.get("output", "projections_file")

    @property
    def output_summary_file(self):
        return self._config.get("output", "summary_file")
