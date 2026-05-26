"""Array manipulation utilities for signal processing.

Provides windowing, overlap operations, and numerical helpers
used throughout the processing stages.
"""
import math


def create_windows(samples, window_size, overlap_ratio):
    """Split a sample array into overlapping windows.

    Args:
        samples: List of float sample values.
        window_size: Number of samples per window.
        overlap_ratio: Fraction of overlap between consecutive windows.
            Value of 0.5 means 50% overlap (hop = window_size / 2).

    Returns:
        List of windows, each a list of float values.
    """
    hop_size = int(window_size * (1 - overlap_ratio))
    windows = []
    i = 0
    while i + window_size <= len(samples):
        window = samples[i:i + window_size]
        windows.append(window)
        i += hop_size
    return windows


def rms_normalize(window):
    """Normalize a window by its RMS (root mean square) value.

    Returns the window scaled so that its RMS equals 1.0.
    If RMS is zero, returns the window unchanged.
    """
    if not window:
        return window
    mean_sq = sum(x * x for x in window) / len(window)
    rms = math.sqrt(mean_sq)
    if rms < 1e-12:
        return window
    return [x / rms for x in window]


def peak_normalize(window):
    """Normalize a window by its peak absolute value."""
    if not window:
        return window
    peak = max(abs(x) for x in window)
    if peak < 1e-12:
        return window
    return [x / peak for x in window]


def compute_energy(window):
    """Compute the energy (sum of squares) of a window."""
    return sum(x * x for x in window)


def compute_rms(window):
    """Compute the RMS value of a window."""
    if not window:
        return 0.0
    return math.sqrt(sum(x * x for x in window) / len(window))


def merge_intervals(intervals, gap_ms):
    """Merge intervals that are within gap_ms of each other.

    Args:
        intervals: List of (start_ms, end_ms) tuples, sorted by start.
        gap_ms: Maximum gap between intervals to merge them.

    Returns:
        List of merged (start_ms, end_ms) tuples.
    """
    if not intervals:
        return []
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if start - prev_end <= gap_ms:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged
