# Geofence Alert Engine — Debugging Task

## Overview
A location-aware alerting system ingests real-time position events from multiple sensor feeds, classifies each event into geofence zones using spatial bounding-box containment, computes per-asset dwell times within those zones across fixed time windows, and fires alerts when dwell thresholds are exceeded. The system currently produces incorrect output — some feeds are silently dropped, thresholds are wrong, dwell calculations are inflated, and event ordering is non-deterministic.

## System Environment
- **Language**: Python 3.11
- **Runtime**: `/app/runtime/` (source, config, data, output)
- **Global system-wide tooling**: `uv` and `pytest` are available
- **Entry point**: `python3 -m runtime.run_engine`

## Processing Stages
1. **Configuration Loading** — Reads `/app/runtime/config/settings.ini` to determine active sensor feeds, zone boundaries, and alerting parameters. The realtime alerting section (`alerting.realtime`) provides the operational thresholds for dwell detection.
2. **Event Ingestion** — Reads JSONL files from `/app/runtime/data/` for each active feed, parses timestamps, and merges into a unified event stream sorted by timestamp, then sensor_id, then sequence number for deterministic ordering.
3. **Spatial Classification** — Each event is checked against zone bounding boxes to assign a `zone_id` (or null if outside all zones).
4. **Dwell Tracking** — Events are partitioned into fixed time windows. For each window, per-asset dwell time in each zone is computed. The final dwell value for each asset-zone pair is the dwell from the last window containing that pair (not a sum across windows).
5. **Alert Generation** — Any asset-zone pair whose dwell time exceeds the configured realtime threshold triggers an alert with severity based on the overage amount.
6. **Report Writing** — Outputs four JSON files to `/app/runtime/output/`.

## Problem
The system runs without errors but produces incorrect results. Specifically:
- The processing statistics show fewer feeds than expected — one feed appears to be dropped silently despite being listed in the configuration.
- Alert thresholds do not match what the realtime section specifies, meaning alerts only fire for extreme dwell durations instead of the expected tight threshold.
- Dwell time values are inflated beyond what any single time window should produce.
- When multiple sensor streams report events at the same timestamp, the output event ordering is inconsistent across runs.

## Expected Correct Output
When all defects are fixed, the system should:
- Process events from all four configured feeds (gps_north, gps_south, gps_east, beacon_west)
- Use the realtime dwell threshold of 25 seconds
- Report dwell times that reflect only the final time window for each asset-zone pair
- Produce deterministic event ordering using timestamp, sensor_id, then sequence number as tiebreakers
- Generate alerts with correct severity levels based on the 25-second threshold

## Output Schema

### `/app/runtime/output/event_log.json`
| Field | Type | Description |
|-------|------|-------------|
| `events` | array | List of processed event records |
| `events[].timestamp` | string | ISO-8601 timestamp of the event |
| `events[].sensor_id` | string | Identifier of the reporting sensor |
| `events[].seq` | integer | Sequence number within the sensor stream |
| `events[].asset_id` | string | Identifier of the tracked asset |
| `events[].lat` | float | Latitude coordinate |
| `events[].lon` | float | Longitude coordinate |
| `events[].zone_id` | string or null | Geofence zone containing this point |
| `events[].feed` | string | Source feed name |
| `total_count` | integer | Total number of events processed |

### `/app/runtime/output/dwell_summary.json`
| Field | Type | Description |
|-------|------|-------------|
| `dwell_records` | array | List of asset-zone dwell entries |
| `dwell_records[].asset_id` | string | Asset identifier |
| `dwell_records[].zone_id` | string | Zone where dwell occurred |
| `dwell_records[].total_dwell_seconds` | float | Dwell duration in seconds |
| `record_count` | integer | Number of dwell records |

### `/app/runtime/output/alerts.json`
| Field | Type | Description |
|-------|------|-------------|
| `alerts` | array | List of triggered alerts |
| `alerts[].alert_type` | string | Always "dwell_exceeded" |
| `alerts[].asset_id` | string | Asset that triggered the alert |
| `alerts[].zone_id` | string | Zone where threshold was exceeded |
| `alerts[].dwell_seconds` | float | Actual dwell time observed |
| `alerts[].threshold_seconds` | integer | Configured threshold value |
| `alerts[].last_seen` | string | ISO timestamp of last event in zone |
| `alerts[].severity` | string | One of "medium", "high", "critical" |
| `alert_count` | integer | Number of alerts generated |

### `/app/runtime/output/stats.json`
| Field | Type | Description |
|-------|------|-------------|
| `total_events_processed` | integer | Count of all ingested events |
| `active_feeds_count` | integer | Number of feeds actually processed |
| `feeds_processed` | array | List of feed name strings |
| `zones_with_activity` | array | Zone IDs that had events |
| `unique_assets` | array | Distinct asset IDs seen |
| `dwell_records_count` | integer | Number of dwell entries |
| `alerts_generated` | integer | Number of alerts fired |

## Key Files
| File | Purpose |
|------|---------|
| `/app/runtime/run_engine.py` | Main entry point orchestrating the workflow |
| `/app/runtime/config_loader.py` | Reads settings.ini and exposes config properties |
| `/app/runtime/event_ingestor.py` | Reads JSONL feeds and produces sorted event list |
| `/app/runtime/spatial_index.py` | Bounding-box zone containment checks |
| `/app/runtime/dwell_tracker.py` | Time-window partitioning and dwell computation |
| `/app/runtime/alert_generator.py` | Threshold comparison and alert record creation |
| `/app/runtime/report_writer.py` | JSON output file generation |
| `/app/runtime/config/settings.ini` | Configuration with sensor feeds, zones, thresholds |
| `/app/runtime/data/*.jsonl` | Raw sensor event data files |

## Your Task
Identify and fix the defects in the runtime source files so that the engine produces correct output matching the schema and behavior described above. The bugs are in the processing logic — not in the data files, spatial index, or report writer.
