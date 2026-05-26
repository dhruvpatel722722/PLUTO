"""Configuration reader with section-aware parameter resolution.

Supports hierarchical sections where child sections (e.g., analysis.detector)
specialize parent sections (e.g., analysis). Parameter resolution follows
child-first lookup with parent fallback.
"""
import configparser
import os


class SignalConfig:
    """Reads and resolves signal processing configuration.

    Section hierarchy:
    - [acquisition]: Input data parameters
    - [processing]: Window and normalization settings
    - [processing.filter]: Band-pass filter configuration
    - [analysis]: General anomaly detection parameters
    - [analysis.detector]: Detector-specific overrides
    - [output]: Output file settings
    """

    _DETECTOR_SECTION = "analysis"

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config", "settings.ini"
            )
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._channel_cache = None

    @property
    def data_directory(self):
        return self._config.get("acquisition", "data_directory")

    @property
    def sample_rate(self):
        return self._config.getint("acquisition", "sample_rate")

    @property
    def channels(self):
        """Return set of active channel identifiers."""
        if self._channel_cache is None:
            raw = self._config.get("acquisition", "channels")
            self._channel_cache = set(raw.split(","))
        return self._channel_cache

    @property
    def window_size(self):
        return self._config.getint("processing", "window_size")

    @property
    def overlap_ratio(self):
        return self._config.getfloat("processing", "overlap_ratio")

    @property
    def normalization_mode(self):
        """Get the normalization mode for windowed data.

        The processing.window section contains the active normalization
        setting. Modes: 'rms', 'peak', or 'none'.
        """
        return self._config.get("processing", "normalization")

    @property
    def filter_type(self):
        return self._config.get("processing.filter", "type")

    @property
    def filter_low_cutoff(self):
        return self._config.getfloat("processing.filter", "low_cutoff")

    @property
    def filter_high_cutoff(self):
        return self._config.getfloat("processing.filter", "high_cutoff")

    @property
    def filter_order(self):
        return self._config.getint("processing.filter", "order")

    def get_detector_param(self, key, as_type=float):
        """Retrieve a parameter from the detector configuration.

        Resolves from the detector section hierarchy.
        """
        raw = self._config.get(self._DETECTOR_SECTION, key)
        return as_type(raw)

    @property
    def merge_window_ms(self):
        return self.get_detector_param("merge_window_ms", as_type=float)

    @property
    def min_duration_ms(self):
        return self._config.getfloat("analysis.detector", "min_duration_ms")

    @property
    def output_directory(self):
        return self._config.get("output", "output_directory")

    @property
    def detections_file(self):
        return self._config.get("output", "detections_file")

    @property
    def summary_file(self):
        return self._config.get("output", "summary_file")
