"""Tests for the CQRS event replay engine output correctness."""
import json
import os

import pytest


PROJECTIONS_PATH = "/app/runtime/output/projections.json"
SUMMARY_PATH = "/app/runtime/output/replay_summary.json"


def load_projections():
    """Load projections output file."""
    with open(PROJECTIONS_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load replay summary output file."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (pass even with buggy code) ---


class TestOutputStructure:
    """Verify basic output file existence and structure."""

    def test_projections_file_exists(self):
        """Projections output file must exist at the expected path."""
        assert os.path.isfile(PROJECTIONS_PATH), (
            f"Expected projections file at {PROJECTIONS_PATH}"
        )

    def test_summary_file_exists(self):
        """Summary output file must exist at the expected path."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected summary file at {SUMMARY_PATH}"
        )

    def test_projections_is_valid_json_array(self):
        """Projections output must be a valid JSON array."""
        data = load_projections()
        assert isinstance(data, list), "projections.json must be a JSON array"
        assert len(data) > 0, "projections.json must not be empty"

    def test_summary_has_required_fields(self):
        """Summary output must contain all required schema fields."""
        summary = load_summary()
        required_fields = [
            "total_ingested",
            "total_filtered",
            "total_processed",
            "batch_count",
            "projection_count",
            "event_ordering",
        ]
        for field in required_fields:
            assert field in summary, (
                f"Missing required field '{field}' in replay_summary.json"
            )


# --- MEDIUM TESTS (require 1-2 bug fixes) ---


class TestEventFiltering:
    """Verify event type filtering works correctly."""

    def test_total_ingested_count(self):
        """All 55 events from 3 stream files must be ingested."""
        summary = load_summary()
        assert summary["total_ingested"] == 55, (
            f"Expected 55 total ingested events (20 orders + 18 payments + 17 inventory), "
            f"got {summary['total_ingested']}. Check /app/runtime/event_ingestor.py"
        )

    def test_all_event_types_included_after_filter(self):
        """All 55 events must pass filtering when all 4 types are accepted.

        The accepted_event_types config must include: order_placed,
        payment_received, inventory_adjusted, and shipment_dispatched.
        Check /app/runtime/config/settings.ini for whitespace issues in the list.
        """
        summary = load_summary()
        assert summary["total_filtered"] == 55, (
            f"Expected 55 filtered events (all types accepted), got "
            f"{summary['total_filtered']}. Check accepted_event_types parsing "
            f"in /app/runtime/config_loader.py — ensure items are stripped of whitespace"
        )

    def test_correct_batch_count(self):
        """With 55 events and batch_size=10, there should be 6 batches.

        The batch_size should come from the [replay.projection] config section.
        """
        summary = load_summary()
        assert summary["batch_count"] == 6, (
            f"Expected 6 batches (55 events / batch_size 10), got "
            f"{summary['batch_count']}. Check which config section batch_size "
            f"is read from in /app/runtime/config_loader.py"
        )


# --- HARD TESTS (require 3-4 bug fixes together) ---


class TestProjectionAccuracy:
    """Verify projection values are computed correctly."""

    def test_projection_count(self):
        """Must produce exactly 4 aggregate projections."""
        projections = load_projections()
        assert len(projections) == 4, (
            f"Expected 4 projections (agg_001..agg_004), got {len(projections)}"
        )

    def test_aggregate_event_counts(self):
        """Each aggregate must have correct event_count reflecting all processed events.

        agg_001: 16 events, agg_002: 14 events, agg_003: 14 events, agg_004: 11 events.
        """
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}

        expected_counts = {
            "agg_001": 16,
            "agg_002": 14,
            "agg_003": 14,
            "agg_004": 11,
        }
        for agg_id, expected in expected_counts.items():
            actual = proj_map[agg_id]["event_count"]
            assert actual == expected, (
                f"{agg_id}: expected event_count={expected}, got {actual}. "
                f"Ensure all event types are included and batch_size is correct."
            )

    def test_aggregate_quantities(self):
        """Projection quantities must reflect last-write-wins per batch, not accumulation.

        Expected: agg_001=5, agg_002=0, agg_003=8, agg_004=3.
        If values are inflated, check /app/runtime/projection_builder.py batch
        snapshot application logic — should replace, not accumulate.
        """
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}

        expected_quantities = {
            "agg_001": 5,
            "agg_002": 0,
            "agg_003": 8,
            "agg_004": 3,
        }
        for agg_id, expected in expected_quantities.items():
            actual = proj_map[agg_id]["quantity"]
            assert actual == expected, (
                f"{agg_id}: expected quantity={expected}, got {actual}. "
                f"Check snapshot application in /app/runtime/projection_builder.py — "
                f"batch snapshots should replace projection state, not accumulate."
            )

    def test_aggregate_total_amounts(self):
        """Projection total_amount must reflect last-write-wins per batch.

        Expected: agg_001=12.50, agg_002=29.97, agg_003=79.92, agg_004=29.97.
        """
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}

        expected_amounts = {
            "agg_001": 12.50,
            "agg_002": 29.97,
            "agg_003": 79.92,
            "agg_004": 29.97,
        }
        for agg_id, expected in expected_amounts.items():
            actual = proj_map[agg_id]["total_amount"]
            assert abs(actual - expected) < 0.01, (
                f"{agg_id}: expected total_amount={expected}, got {actual}. "
                f"Check snapshot application and event ordering in "
                f"/app/runtime/projection_builder.py and /app/runtime/event_sorter.py"
            )

    def test_deterministic_ordering(self):
        """Events with same timestamp from different streams must sort by _stream_id.

        The event_ordering field must be 'timestamp_stream_seq'.
        Check /app/runtime/event_sorter.py — sort key must include _stream_id
        between timestamp and seq for deterministic replay.
        """
        summary = load_summary()
        assert summary["event_ordering"] == "timestamp_stream_seq", (
            f"Expected event_ordering='timestamp_stream_seq', "
            f"got '{summary['event_ordering']}'"
        )
        # Verify deterministic output via last_updated timestamps
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        assert proj_map["agg_001"]["last_updated"] == "2024-01-15T08:00:37Z", (
            f"agg_001 last_updated should be '2024-01-15T08:00:37Z', got "
            f"'{proj_map['agg_001']['last_updated']}'. "
            f"Check sort order in /app/runtime/event_sorter.py — must include "
            f"_stream_id for deterministic ordering when timestamps collide."
        )

    def test_full_summary_correctness(self):
        """Complete summary must match expected values with all bugs fixed."""
        summary = load_summary()
        assert summary["total_ingested"] == 55, (
            f"total_ingested: expected 55, got {summary['total_ingested']}"
        )
        assert summary["total_filtered"] == 55, (
            f"total_filtered: expected 55, got {summary['total_filtered']}"
        )
        assert summary["total_processed"] == 55, (
            f"total_processed: expected 55, got {summary['total_processed']}"
        )
        assert summary["batch_count"] == 6, (
            f"batch_count: expected 6, got {summary['batch_count']}"
        )
        assert summary["projection_count"] == 4, (
            f"projection_count: expected 4, got {summary['projection_count']}"
        )
