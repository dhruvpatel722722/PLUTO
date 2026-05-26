"""Configuration loader for the event replay engine.

Reads settings from the INI configuration file and provides typed access
to all configuration parameters. Uses a two-phase loading approach:
first reads raw values, then resolves derived configuration on demand.

The configuration is organized into hierarchical sections where child
sections (e.g., replay.engine) specialize parent sections (e.g., replay).
"""
import configparser
import os

from runtime.utils.text_parser import parse_csv_set


class ReplayConfig:
    """Loads and provides access to replay engine configuration.

    Configuration sections:
    - [sources]: Data input paths and format
    - [sources.filter]: Event type filtering rules
    - [replay]: General replay parameters
    - [replay.engine]: Engine-specific batch and snapshot settings
    - [output]: Output file configuration

    Engine parameters are accessed through get_engine_param() which
    resolves values from the engine-specific section hierarchy.
    """

    _ENGINE_SECTION = "replay"

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "settings.ini"
            )
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._type_cache = None
        self._raw_filter_value = self._config.get("sources.filter", "accepted_types")

    def _resolve_types(self):
        """Resolve accepted event types from cached raw config value."""
        if self._type_cache is None:
            self._type_cache = parse_csv_set(self._raw_filter_value)
        return self._type_cache

    @property
    def data_directory(self):
        return self._config.get("sources", "data_directory")

    @property
    def output_directory(self):
        return self._config.get("sources", "output_directory")

    @property
    def accepted_event_types(self):
        """Return set of event types that pass the filter stage."""
        return self._resolve_types()

    @property
    def batch_size(self):
        """Direct access to engine batch size (used by internal modules)."""
        return self._config.getint("replay.engine", "batch_size")

    def get_engine_param(self, key, as_type=int):
        """Retrieve a parameter from the engine configuration section.

        Resolves parameters from the replay engine hierarchy. Used by
        the orchestration layer to configure processing components.

        Args:
            key: Parameter name to retrieve
            as_type: Type to coerce value to (default: int)

        Returns:
            Configuration value coerced to requested type.
        """
        raw = self._config.get(self._ENGINE_SECTION, key)
        return as_type(raw)

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
