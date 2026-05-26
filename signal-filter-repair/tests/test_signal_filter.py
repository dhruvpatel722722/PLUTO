"""Tests for the multi-channel signal processing engine.

Validates correct signal acquisition, windowing, filtering, and
anomaly detection across all configured channels.
"""
import json
import os

import pytest


DETECTIONS_PATH = "/app/runtime/output/detections.json"
SUMMARY_PATH = "/app/runtime/output/processing_summary.json"


def load_detections():
    with open(DETECTIONS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


class TestOutputStructure:
    """Verify output files exist and have correct schema."""

    def test_detections_file_exists(self):
        """Detection output must be generated."""
        assert os.path.isfile(DETECTIONS_PATH)

    def test_summary_file_exists(self):
        """Summary output must be generated."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_detections_is_list(self):
        """Detections must be a JSON array."""
        data = load_detections()
        assert isinstance(data, list)

    def test_summary_has_required_fields(self):
        """Summary must contain all processing statistics."""
        summary = load_summary()
        required = {"total_samples_read", "channels_available",
                    "channels_selected", "channels_rejected",
                    "total_windows", "total_filtered_windows",
                    "raw_flags", "detection_count", "processing_config"}
        assert required.issubset(set(summary.keys()))


class TestChannelSelection:
    """Verify correct channel acquisition and selection."""

    def test_all_channels_available(self):
        """All four sensor channels must be read from data directory."""
        summary = load_summary()
        assert sorted(summary["channels_available"]) == ["east", "north", "south", "west"]

    def test_all_channels_selected(self):
        """All four channels must pass the selection filter."""
        summary = load_summary()
        assert sorted(summary["channels_selected"]) == ["east", "north", "south", "west"]

    def test_no_channels_rejected(self):
        """No channels should be rejected when properly configured."""
        summary = load_summary()
        assert summary["channels_rejected"] == []

    def test_total_samples(self):
        """1024 total samples must be read (4 channels x 256 samples)."""
        summary = load_summary()
        assert summary["total_samples_read"] == 1024


class TestWindowProcessing:
    """Verify windowing and filtering stage outputs."""

    def test_total_window_count(self):
        """With 4 channels of 256 samples, window_size=64, overlap=0.5: 28 windows."""
        summary = load_summary()
        assert summary["total_windows"] == 28

    def test_filtered_window_count(self):
        """All windows must pass through the filter stage."""
        summary = load_summary()
        assert summary["total_filtered_windows"] == 28

    def test_normalization_mode(self):
        """Processing must use 'none' normalization mode."""
        summary = load_summary()
        assert summary["processing_config"]["normalization"] == "none"

    def test_threshold_sigma_value(self):
        """Detector must use sigma threshold of 1.5."""
        summary = load_summary()
        assert summary["processing_config"]["threshold_sigma"] == 1.5

    def test_merge_window_value(self):
        """Detector must use merge window of 25ms."""
        summary = load_summary()
        assert summary["processing_config"]["merge_window_ms"] == 25.0


class TestDetectionAccuracy:
    """Verify anomaly detection produces correct results."""

    def test_raw_flag_count(self):
        """Exactly 4 windows must exceed the energy threshold."""
        summary = load_summary()
        assert summary["raw_flags"] == 4

    def test_detection_count(self):
        """Exactly 3 merged detections must be produced."""
        summary = load_summary()
        assert summary["detection_count"] == 3

    def test_detection_channels(self):
        """Detections must come from east, north, and west channels."""
        detections = load_detections()
        channels = sorted(set(d["channel_id"] for d in detections))
        assert channels == ["east", "north", "west"]

    def test_detection_intervals(self):
        """Detection time intervals must match expected values."""
        detections = load_detections()
        expected = [
            {"channel_id": "east", "start_ms": 64.0, "end_ms": 128.0, "duration_ms": 64.0},
            {"channel_id": "north", "start_ms": 96.0, "end_ms": 160.0, "duration_ms": 64.0},
            {"channel_id": "west", "start_ms": 160.0, "end_ms": 256.0, "duration_ms": 96.0},
        ]
        assert len(detections) == len(expected)
        for det, exp in zip(detections, expected):
            assert det["channel_id"] == exp["channel_id"]
            assert abs(det["start_ms"] - exp["start_ms"]) < 0.1
            assert abs(det["end_ms"] - exp["end_ms"]) < 0.1
            assert abs(det["duration_ms"] - exp["duration_ms"]) < 0.1

    def test_detection_ordering(self):
        """Detections must be in chronological order with channel tiebreak."""
        detections = load_detections()
        for i in range(1, len(detections)):
            prev = detections[i-1]
            curr = detections[i]
            assert (curr["start_ms"], curr["channel_id"]) >= (prev["start_ms"], prev["channel_id"])
