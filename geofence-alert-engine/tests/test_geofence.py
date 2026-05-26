"""Tests for the geofence alert engine output correctness."""
import json
import os

OUTPUT_DIR = "/app/runtime/output"


def _load_json(filename):
    """Load a JSON output file."""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


# --- Easy tests (pass even with buggy code) ---

def test_output_files_exist():
    """Verify all four expected output files are created."""
    expected_files = ["event_log.json", "dwell_summary.json", "alerts.json", "stats.json"]
    for fname in expected_files:
        path = os.path.join(OUTPUT_DIR, fname)
        assert os.path.isfile(path), f"Missing output file: {fname}"


def test_event_log_structure():
    """Verify event_log.json has the required top-level keys and record structure."""
    data = _load_json("event_log.json")
    assert "events" in data, "event_log.json missing 'events' key"
    assert "total_count" in data, "event_log.json missing 'total_count' key"
    assert isinstance(data["events"], list), "'events' must be a list"
    assert data["total_count"] == len(data["events"]), "total_count must match events length"
    if data["events"]:
        record = data["events"][0]
        required_fields = {"timestamp", "sensor_id", "seq", "asset_id", "lat", "lon", "zone_id", "feed"}
        assert required_fields.issubset(record.keys()), (
            f"Event record missing fields: {required_fields - set(record.keys())}"
        )


def test_stats_file_structure():
    """Verify stats.json has all required summary fields."""
    data = _load_json("stats.json")
    required_keys = {
        "total_events_processed", "active_feeds_count", "feeds_processed",
        "zones_with_activity", "unique_assets", "dwell_records_count", "alerts_generated"
    }
    assert required_keys.issubset(data.keys()), (
        f"stats.json missing keys: {required_keys - set(data.keys())}"
    )


def test_dwell_summary_structure():
    """Verify dwell_summary.json structure and field names."""
    data = _load_json("dwell_summary.json")
    assert "dwell_records" in data, "dwell_summary.json missing 'dwell_records' key"
    assert "record_count" in data, "dwell_summary.json missing 'record_count' key"
    if data["dwell_records"]:
        record = data["dwell_records"][0]
        required_fields = {"asset_id", "zone_id", "total_dwell_seconds"}
        assert required_fields.issubset(record.keys()), (
            f"Dwell record missing fields: {required_fields - set(record.keys())}"
        )


# --- Medium tests (require 1-2 bug fixes) ---

def test_all_feeds_processed():
    """Verify that all configured feeds including beacon_west are processed.

    The config lists four active feeds. If any feed is silently dropped due to
    whitespace in the comma-separated list, this test catches it.
    Check /app/runtime/config_loader.py for how active_feeds are parsed.
    """
    data = _load_json("stats.json")
    expected_feeds = {"gps_north", "gps_south", "gps_east", "beacon_west"}
    actual_feeds = set(data["feeds_processed"])
    assert expected_feeds.issubset(actual_feeds), (
        f"Missing feeds: {expected_feeds - actual_feeds}. "
        f"Check feed name parsing in /app/runtime/config_loader.py — "
        f"whitespace around comma-separated values may cause mismatches."
    )
    assert data["active_feeds_count"] >= 4, (
        f"Expected at least 4 active feeds, got {data['active_feeds_count']}"
    )


def test_alert_threshold_matches_realtime():
    """Verify alerts use the realtime threshold of 25 seconds, not 300.

    The alerting.realtime section defines operational thresholds.
    Check /app/runtime/config_loader.py for which section is read.
    """
    data = _load_json("alerts.json")
    if data["alert_count"] > 0:
        for alert in data["alerts"]:
            assert alert["threshold_seconds"] == 25, (
                f"Alert threshold is {alert['threshold_seconds']} but should be 25. "
                f"Check /app/runtime/config_loader.py — the realtime section "
                f"(alerting.realtime) should be used, not the general alerting section."
            )


def test_dwell_values_within_window_bounds():
    """Verify dwell times reflect single-window values, not accumulated sums.

    With a 60-second time window, no single-window dwell can exceed 60 seconds.
    If values exceed this, the tracker is summing across windows incorrectly.
    Check /app/runtime/dwell_tracker.py compute_dwell_times method.
    """
    data = _load_json("dwell_summary.json")
    for record in data["dwell_records"]:
        assert record["total_dwell_seconds"] <= 60.0, (
            f"Dwell for {record['asset_id']} in {record['zone_id']} is "
            f"{record['total_dwell_seconds']}s which exceeds the 60s window. "
            f"Check /app/runtime/dwell_tracker.py — dwell should use the final "
            f"window value, not accumulate across windows."
        )


# --- Hard tests (require 3-4 bug fixes together) ---

def test_event_ordering_deterministic():
    """Verify events are sorted by timestamp, then sensor_id, then seq.

    When events share the same timestamp from different sensors, ordering
    must be deterministic. The sort key must include sensor_id as a tiebreaker.
    Note: seq is local to each sensor stream, so it alone cannot break ties.
    """
    data = _load_json("event_log.json")
    events = data["events"]
    for i in range(1, len(events)):
        prev = events[i - 1]
        curr = events[i]
        prev_key = (prev["timestamp"], prev["sensor_id"], prev["seq"])
        curr_key = (curr["timestamp"], curr["sensor_id"], curr["seq"])
        assert prev_key <= curr_key, (
            f"Event ordering violation at index {i}: "
            f"{prev_key} should come before {curr_key}. "
            f"Check /app/runtime/event_ingestor.py sort key — "
            f"sensor_id must be included for deterministic ordering."
        )


def test_beacon_west_events_in_log():
    """Verify beacon_west events appear in the event log with zone assignments.

    This tests the combined effect of feed parsing fix and spatial classification.
    """
    data = _load_json("event_log.json")
    beacon_events = [e for e in data["events"] if e["feed"] == "beacon_west"]
    assert len(beacon_events) == 18, (
        f"Expected 18 beacon_west events, found {len(beacon_events)}. "
        f"The beacon_west feed must be included — check feed name parsing."
    )
    # Some beacon_west events should be in the loading_dock zone
    zoned = [e for e in beacon_events if e["zone_id"] is not None]
    assert len(zoned) > 0, (
        "No beacon_west events were classified into any zone. "
        "Check spatial_index zone boundaries vs beacon coordinates."
    )


def test_alert_severity_computation():
    """Verify alert severity uses the correct 25-second realtime threshold.

    With the correct threshold and non-accumulated dwell:
    - medium: overage < 12.5s (threshold * 0.5)
    - high: overage >= 12.5s but < 25s
    - critical: overage >= 25s (threshold * 1.0)

    This requires correct threshold AND correct dwell values.
    """
    data = _load_json("alerts.json")
    assert data["alert_count"] > 0, (
        "No alerts were generated. The system should produce alerts when assets "
        "dwell longer than 25 seconds in a zone. Check threshold configuration "
        "in /app/runtime/config_loader.py and dwell calculation in "
        "/app/runtime/dwell_tracker.py"
    )
    for alert in data["alerts"]:
        assert alert["severity"] in ("medium", "high", "critical"), (
            f"Invalid severity '{alert['severity']}' for alert on {alert['asset_id']}"
        )
        overage = alert["dwell_seconds"] - alert["threshold_seconds"]
        if overage >= alert["threshold_seconds"]:
            expected = "critical"
        elif overage >= alert["threshold_seconds"] * 0.5:
            expected = "high"
        else:
            expected = "medium"
        assert alert["severity"] == expected, (
            f"Alert severity mismatch for {alert['asset_id']} in {alert['zone_id']}: "
            f"got '{alert['severity']}', expected '{expected}' "
            f"(dwell={alert['dwell_seconds']}, threshold={alert['threshold_seconds']})"
        )
