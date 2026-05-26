"""Windowing stage: segments continuous signals into analysis frames.

Takes raw channel samples and produces overlapping windows suitable
for spectral analysis and feature extraction.
"""
from runtime.utils.array_ops import create_windows, rms_normalize, peak_normalize


class WindowingStage:
    """Segments channel signals into overlapping normalized windows.

    Processing per channel:
    1. Extract amplitude values from sample records
    2. Divide into overlapping windows
    3. Normalize each window according to configured mode
    """

    def __init__(self, config):
        self._window_size = config.window_size
        self._overlap = config.overlap_ratio
        self._norm_mode = config.normalization_mode
        self._results = {}
        self._total_windows = 0

    def process(self, channel_data):
        """Window and normalize all channels.

        Args:
            channel_data: Dict mapping channel_id to list of sample records.

        Returns:
            Dict mapping channel_id to list of normalized windows.
        """
        self._results = {}
        self._total_windows = 0

        for channel_id, samples in sorted(channel_data.items()):
            # Extract raw amplitude values
            values = [s["value"] for s in samples]

            # Create overlapping windows
            windows = create_windows(values, self._window_size, self._overlap)

            # Normalize each window
            normalized = []
            for w in windows:
                if self._norm_mode == "rms":
                    normalized.append(rms_normalize(w))
                elif self._norm_mode == "peak":
                    normalized.append(peak_normalize(w))
                else:
                    normalized.append(w)

            self._results[channel_id] = normalized
            self._total_windows += len(normalized)

        return self._results

    @property
    def total_windows(self):
        return self._total_windows

    @property
    def channel_window_counts(self):
        return {ch: len(wins) for ch, wins in self._results.items()}
