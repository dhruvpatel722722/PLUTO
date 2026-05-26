"""Tests for the CQRS event replay engine output correctness.

Validates that the replay engine correctly processes events through all
stages and produces accurate aggregate projections and summary statistics.
"""
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


# --- STRUCTURAL TESTS (always pass) ---


class TestOutputIntegrity:
    """Verify output files exist and conform to expected schema."""

    def test_projections_file_exists(self):
        """Output projections file must be generated at expected location."""
        assert os.path.isfile(PROJECTIONS_PATH), (
            "Projections output was not generated"
        )

    def test_summary_file_exists(self):
        """Output summary file must be generated at expected location."""
        assert os.path.isfile(SUMMARY_PATH), (
            "Summary output was not generated"
        )

    def test_projections_schema_compliance(self):
        """Each projection entry must contain all required fields."""
        projections = load_projections()
        required = {"aggregate_id", "quantity", "total_amount",
                    "event_count", "last_updated", "streams_seen"}
        for proj in projections:
            missing = required - set(proj.keys())
            assert not missing, (
                f"Projection entry missing required fields: {missing}"
            )

    def test_summary_schema_compliance(self):
        """Summary must contain all required statistical fields."""
        summary = load_summary()
        required = {"total_ingested", "total_filtered", "total_rejected",
                    "total_processed", "batch_count", "batch_size_used",
                    "projection_count", "accumulation_mode", "event_ordering"}
        missing = required - set(summary.keys())
        assert not missing, (
            f"Summary missing required fields: {missing}"
        )


# --- EVENT PROCESSING TESTS ---


class TestEventProcessing:
    """Verify event ingestion, filtering, and processing counts."""

    def test_ingestion_completeness(self):
        """All 55 raw events from source streams must be ingested."""
        summary = load_summary()
        assert summary["total_ingested"] == 55, (
            f"Expected 55 ingested events, got {summary['total_ingested']}"
        )

    def test_no_events_rejected(self):
        """When all event types are properly accepted, rejection count is zero."""
        summary = load_summary()
        assert summary["total_rejected"] == 0, (
            f"Expected 0 rejected events, got {summary['total_rejected']}"
        )

    def test_all_events_pass_filter(self):
        """Filtered count must equal ingested count when all types accepted."""
        summary = load_summary()
        assert summary["total_filtered"] == 55, (
            f"Expected 55 filtered events, got {summary['total_filtered']}"
        )

    def test_all_filtered_events_processed(self):
        """Every filtered event must be processed during projection building."""
        summary = load_summary()
        assert summary["total_processed"] == 55, (
            f"Expected 55 processed events, got {summary['total_processed']}"
        )


# --- BATCH CONFIGURATION TESTS ---


class TestBatchConfiguration:
    """Verify batch processing configuration and execution."""

    def test_batch_size_value(self):
        """Engine must use batch size of 10 for projection building."""
        summary = load_summary()
        assert summary["batch_size_used"] == 10, (
            f"Expected batch_size_used=10, got {summary['batch_size_used']}"
        )

    def test_batch_count(self):
        """With 55 events and batch size 10, must produce 6 complete batches."""
        summary = load_summary()
        assert summary["batch_count"] == 6, (
            f"Expected 6 batches, got {summary['batch_count']}"
        )

    def test_accumulation_mode_reported(self):
        """Engine must report the configured accumulation mode."""
        summary = load_summary()
        assert summary["accumulation_mode"] == "replace", (
            f"Expected accumulation_mode='replace', got '{summary['accumulation_mode']}'"
        )


# --- PROJECTION ACCURACY TESTS ---


class TestProjectionValues:
    """Verify computed projection values match expected correct output.

    These values depend on correct filtering (all events included),
    correct batch sizing (10 per batch), correct ordering (deterministic),
    and correct accumulation mode (replace, not accumulate).
    """

    def test_aggregate_count(self):
        """Must produce exactly 4 unique aggregate projections."""
        projections = load_projections()
        assert len(projections) == 4, (
            f"Expected 4 aggregates, got {len(projections)}"
        )

    def test_event_counts_per_aggregate(self):
        """Each aggregate must have processed the correct number of events."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {"agg_001": 16, "agg_002": 14, "agg_003": 14, "agg_004": 11}
        for agg_id, count in expected.items():
            assert proj_map[agg_id]["event_count"] == count, (
                f"{agg_id}: expected event_count={count}, "
                f"got {proj_map[agg_id]['event_count']}"
            )

    def test_quantity_values(self):
        """Projection quantities must reflect correct batch snapshot semantics."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {"agg_001": 5, "agg_002": 0, "agg_003": 8, "agg_004": 3}
        for agg_id, qty in expected.items():
            assert proj_map[agg_id]["quantity"] == qty, (
                f"{agg_id}: expected quantity={qty}, "
                f"got {proj_map[agg_id]['quantity']}"
            )

    def test_total_amount_values(self):
        """Projection monetary totals must reflect correct batch semantics."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {"agg_001": 12.50, "agg_002": 29.97,
                    "agg_003": 79.92, "agg_004": 29.97}
        for agg_id, amount in expected.items():
            assert abs(proj_map[agg_id]["total_amount"] - amount) < 0.01, (
                f"{agg_id}: expected total_amount={amount}, "
                f"got {proj_map[agg_id]['total_amount']}"
            )

    def test_stream_coverage_per_aggregate(self):
        """Every aggregate must have received events from all three streams."""
        projections = load_projections()
        expected_streams = ["inventory_stream", "orders_stream", "payments_stream"]
        for proj in projections:
            assert sorted(proj["streams_seen"]) == expected_streams, (
                f"{proj['aggregate_id']}: expected streams {expected_streams}, "
                f"got {sorted(proj['streams_seen'])}"
            )

    def test_last_updated_timestamps(self):
        """Last updated must reflect the chronologically latest event per aggregate."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {
            "agg_001": "2024-01-15T08:00:37Z",
            "agg_002": "2024-01-15T08:00:37Z",
            "agg_003": "2024-01-15T08:00:39Z",
            "agg_004": "2024-01-15T08:00:37Z",
        }
        for agg_id, ts in expected.items():
            assert proj_map[agg_id]["last_updated"] == ts, (
                f"{agg_id}: expected last_updated='{ts}', "
                f"got '{proj_map[agg_id]['last_updated']}'"
            )
