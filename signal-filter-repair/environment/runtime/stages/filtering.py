"""Filtering stage: applies bandpass filter to windowed signal data.

Removes out-of-band noise while preserving signal components within
the configured frequency passband.
"""
from runtime.core.bandpass import BandpassFilter


class FilteringStage:
    """Applies bandpass filter to each window across all channels."""

    def __init__(self, config):
        self._filter = BandpassFilter(
            low_cutoff=config.filter_low_cutoff,
            high_cutoff=config.filter_high_cutoff,
            sample_rate=config.sample_rate,
            order=config.filter_order,
        )
        self._results = {}
        self._total_filtered = 0

    def process(self, windowed_data):
        """Apply bandpass filter to all windows in all channels.

        Args:
            windowed_data: Dict mapping channel_id to list of windows.

        Returns:
            Dict mapping channel_id to list of filtered windows.
        """
        self._results = {}
        self._total_filtered = 0

        for channel_id, windows in sorted(windowed_data.items()):
            filtered_windows = []
            for window in windows:
                filtered = self._filter.apply(window)
                filtered_windows.append(filtered)
                self._total_filtered += 1
            self._results[channel_id] = filtered_windows

        return self._results

    @property
    def total_filtered(self):
        return self._total_filtered
