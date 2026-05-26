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


# --- STRUCTURAL TESTS ---


class TestOutputIntegrity:
    """Verify output files exist and conform to expected schema."""

    def test_projections_file_exists(self):
        """Output projections file must be generated."""
        assert os.path.isfile(PROJECTIONS_PATH), (
            "Projections output was not generated"
        )

    def test_summary_file_exists(self):
        """Output summary file must be generated."""
        assert os.path.isfile(SUMMARY_PATH), (
            "Summary output was not generated"
        )

    def test_projections_schema_compliance(self):
        """Each projection must contain all required fields."""
        projections = load_projections()
        required_fields = {"aggregate_id", "quantity", "total_amount",
                          "event_count", "last_updated", "streams_seen"}
        for proj in projections:
            missing = required_fields - set(proj.keys())
            assert not missing, (
                f"Projection missing fields: {missing}"
            )

    def test_summary_schema_compliance(self):
        """Summary must contain all required statistical fields."""
        summary = load_summary()
        required_fields = {"total_ingested", "total_filtered", "total_rejected",
                          "total_processed", "batch_count", "batch_size_used",
                          "projection_count", "accumulation_mode", "event_ordering"}
        missing = required_fields - set(summary.keys())
        assert not missing, (
            f"Summary missing fields: {missing}"
        )


# --- EVENT CONSERVATION TESTS ---


class TestEventConservation:
    """Verify event counting and filtering correctness."""

    def test_ingestion_completeness(self):
        """All 55 events from 3 stream files must be counted as ingested."""
        summary = load_summary()
        assert summary["total_ingested"] == 55, (
            f"Ingestion count mismatch: expected 55, got {summary['total_ingested']}"
        )

    def test_filter_acceptance_rate(self):
        """With all four event types accepted, zero events should be rejected."""
        summary = load_summary()
        assert summary["total_rejected"] == 0, (
            f"Events were unexpectedly rejected: {summary['total_rejected']} "
            f"rejected out of {summary['total_ingested']} ingested"
        )

    def test_filter_pass_through_count(self):
        """All ingested events must pass the type filter when properly configured."""
        summary = load_summary()
        assert summary["total_filtered"] == 55, (
            f"Filter pass-through mismatch: expected 55, got {summary['total_filtered']}"
        )

    def test_processing_matches_filtered(self):
        """Every filtered event must be processed in projection building."""
        summary = load_summary()
        assert summary["total_processed"] == summary["total_filtered"], (
            f"Processing gap: {summary['total_filtered']} filtered but "
            f"only {summary['total_processed']} processed"
        )


# --- BATCH CONFIGURATION TESTS ---


class TestBatchProcessing:
    """Verify batch sizing and configuration correctness."""

    def test_batch_size_configuration(self):
        """Engine must use the projection-specific batch size of 10."""
        summary = load_summary()
        assert summary["batch_size_used"] == 10, (
            f"Incorrect batch size: expected 10, got {summary['batch_size_used']}"
        )

    def test_batch_count_from_events(self):
        """With 55 events and batch size 10, exactly 6 batches are expected."""
        summary = load_summary()
        assert summary["batch_count"] == 6, (
            f"Batch count mismatch: expected 6, got {summary['batch_count']}"
        )

    def test_accumulation_mode_is_replace(self):
        """Engine must report 'replace' accumulation mode from config."""
        summary = load_summary()
        assert summary["accumulation_mode"] == "replace", (
            f"Wrong accumulation mode: expected 'replace', got '{summary['accumulation_mode']}'"
        )


# --- PROJECTION ACCURACY TESTS ---


class TestProjectionValues:
    """Verify computed projection values are mathematically correct.

    These tests validate that the engine correctly applies last-write-wins
    semantics within each batch and maintains accurate event counts.
    """

    def test_aggregate_count(self):
        """Must produce exactly 4 aggregate projections."""
        projections = load_projections()
        assert len(projections) == 4, (
            f"Expected 4 aggregates, got {len(projections)}"
        )

    def test_event_count_per_aggregate(self):
        """Each aggregate must reflect the correct number of events processed."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {"agg_001": 16, "agg_002": 14, "agg_003": 14, "agg_004": 11}
        for agg_id, count in expected.items():
            assert proj_map[agg_id]["event_count"] == count, (
                f"{agg_id} event_count: expected {count}, "
                f"got {proj_map[agg_id]['event_count']}"
            )

    def test_quantity_values(self):
        """Projection quantities must reflect last-write-wins batch semantics."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {"agg_001": 5, "agg_002": 0, "agg_003": 8, "agg_004": 3}
        for agg_id, qty in expected.items():
            assert proj_map[agg_id]["quantity"] == qty, (
                f"{agg_id} quantity: expected {qty}, "
                f"got {proj_map[agg_id]['quantity']}"
            )

    def test_total_amount_values(self):
        """Projection amounts must reflect last-write-wins batch semantics."""
        projections = load_projections()
        proj_map = {p["aggregate_id"]: p for p in projections}
        expected = {"agg_001": 12.50, "agg_002": 29.97,
                   "agg_003": 79.92, "agg_004": 29.97}
        for agg_id, amount in expected.items():
            assert abs(proj_map[agg_id]["total_amount"] - amount) < 0.01, (
                f"{agg_id} total_amount: expected {amount}, "
                f"got {proj_map[agg_id]['total_amount']}"
            )

    def test_stream_coverage(self):
        """Each aggregate must have events from all three source streams."""
        projections = load_projections()
        expected_streams = ["inventory_stream", "orders_stream", "payments_stream"]
        for proj in projections:
            assert sorted(proj["streams_seen"]) == expected_streams, (
                f"{proj['aggregate_id']} streams_seen mismatch: "
                f"expected {expected_streams}, got {sorted(proj['streams_seen'])}"
            )

    def test_last_updated_timestamps(self):
        """Last updated must reflect the chronologically final event per aggregate."""
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
                f"{agg_id} last_updated: expected {ts}, "
                f"got {proj_map[agg_id]['last_updated']}"
            )
