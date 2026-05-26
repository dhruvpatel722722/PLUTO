"""Detection stage: identifies anomalous signal regions.

Computes per-window energy metrics and flags windows that exceed
a threshold derived from the statistical baseline of each channel.
Flagged windows are converted to time intervals and merged.
"""
import math
import functools

from runtime.utils.array_ops import compute_energy, merge_intervals


def _compute_aggregation(values, mode):
    """Compute aggregate statistic of a value list.

    Args:
        values: List of float values.
        mode: Aggregation mode ('mean' or 'median').

    Returns:
        Aggregated float value.
    """
    if not values:
        return 0.0
    if mode == "mean":
        return sum(values) / len(values)
    elif mode == "median":
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 0:
            return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        return sorted_vals[n // 2]
    return sum(values) / len(values)


@functools.total_ordering
class DetectionKey:
    """Comparison key for sorting detections deterministically.

    Sorts by start_ms, then by channel_id, then by end_ms.
    Ensures stable ordering when detections from different channels
    share the same start time.
    """

    __slots__ = ("start_ms", "channel_id", "end_ms")

    def __init__(self, detection):
        self.start_ms = detection["start_ms"]
        self.channel_id = detection["channel_id"]
        self.end_ms = detection["end_ms"]

    def __eq__(self, other):
        if not isinstance(other, DetectionKey):
            return NotImplemented
        return (self.start_ms, self.channel_id, self.end_ms) == (
            other.start_ms, other.channel_id, other.end_ms
        )

    def __lt__(self, other):
        if not isinstance(other, DetectionKey):
            return NotImplemented
        return (self.start_ms, self.end_ms) < (other.start_ms, other.end_ms)

    def __hash__(self):
        return hash((self.start_ms, self.channel_id, self.end_ms))


class DetectionStage:
    """Detects anomalous windows using energy-based thresholding."""

    def __init__(self, config):
        self._threshold_sigma = config.get_detector_param(
            "threshold_sigma", as_type=float
        )
        self._aggregation = config.get_detector_param(
            "aggregation", as_type=str
        )
        self._merge_gap = config.merge_window_ms
        self._min_duration = config.min_duration_ms
        self._window_size = config.window_size
        self._overlap = config.overlap_ratio
        self._sample_rate = config.sample_rate
        self._detections = []
        self._raw_flags = 0

    def process(self, filtered_data):
        """Detect anomalies across all channels.

        For each channel:
        1. Compute per-window energy
        2. Calculate baseline (mean energy)
        3. Compute std deviation of energy
        4. Flag windows exceeding baseline + threshold_sigma * std
        5. Convert flags to time intervals
        6. Merge nearby intervals
        7. Filter by minimum duration
        """
        all_detections = []
        self._raw_flags = 0

        for channel_id, windows in sorted(filtered_data.items()):
            # Compute energy per window
            energies = [compute_energy(w) for w in windows]

            if not energies:
                continue

            # Compute baseline statistics using configured aggregation
            baseline = _compute_aggregation(energies, self._aggregation)
            variance = sum((e - baseline) ** 2 for e in energies) / len(energies)
            std_dev = math.sqrt(variance)

            # Threshold
            threshold = baseline + self._threshold_sigma * std_dev

            # Flag windows exceeding threshold
            hop_size = int(self._window_size * (1 - self._overlap))
            ms_per_sample = 1000.0 / self._sample_rate

            intervals = []
            for i, energy in enumerate(energies):
                if energy > threshold:
                    self._raw_flags += 1
                    start_sample = i * hop_size
                    end_sample = start_sample + self._window_size
                    start_ms = start_sample * ms_per_sample
                    end_ms = end_sample * ms_per_sample
                    intervals.append((start_ms, end_ms))

            # Merge nearby intervals
            merged = merge_intervals(intervals, self._merge_gap)

            # Filter by minimum duration and create detection records
            for start_ms, end_ms in merged:
                duration = end_ms - start_ms
                if duration >= self._min_duration:
                    all_detections.append({
                        "channel_id": channel_id,
                        "start_ms": round(start_ms, 2),
                        "end_ms": round(end_ms, 2),
                        "duration_ms": round(duration, 2),
                    })

        # Sort detections deterministically
        self._detections = sorted(all_detections, key=DetectionKey)
        return self._detections

    @property
    def detections(self):
        return list(self._detections)

    @property
    def detection_count(self):
        return len(self._detections)

    @property
    def raw_flags(self):
        return self._raw_flags
