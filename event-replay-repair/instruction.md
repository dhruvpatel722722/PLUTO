# Event Replay Engine — Debugging Task

## Overview

A CQRS event replay engine ingests domain events from multiple source streams, merges and orders them deterministically, then replays them in configurable batches to rebuild aggregate state projections. The system processes order, payment, inventory, and shipment events to produce materialized views for downstream consumers.

## System Environment

- **Language**: Python 3.11
- **Runtime**: `/app/runtime/` (source, config, data, output)
- **Global system-wide tooling**: `uv` and `pytest` are available
- **Configuration**: `/app/runtime/config/settings.ini`
- **Data**: `/app/runtime/data/` (JSONL event streams)
- **Output**: `/app/runtime/output/` (JSON projection and summary files)

## Processing Stages

1. **Stream Reading** — Reads all `.jsonl` files from `/app/runtime/data/`, annotating each event with its source stream identifier (`_stream_id` derived from the filename).

2. **Event Filtering** — Applies the `accepted_types` configuration from the `[sources.filter]` section to retain only recognized event types. The accepted types should be: `order_placed`, `payment_received`, `inventory_adjusted`, and `shipment_dispatched`.

3. **Deterministic Sorting** — Orders all filtered events for reproducible replay. The correct ordering uses `timestamp` as primary key, then `_stream_id` (source file identifier) as secondary key, then `seq` (sequence within stream) as tertiary key. This three-part key ensures identical replay ordering even when events from different streams share the same timestamp.

4. **Batch Projection** — Replays events in fixed-size batches configured in the `[replay.engine]` section. Within each batch, the last event value per aggregate wins (snapshot semantics). After batch processing, snapshot values are applied to the running projection state according to the `accumulation_mode` setting (`replace` means overwrite, not add).

5. **Report Generation** — Writes `/app/runtime/output/projections.json` and `/app/runtime/output/replay_summary.json`.

## Problem

The engine runs without errors but produces incorrect output. Some event types are silently dropped during filtering, batch boundaries are incorrect, computed projection values are inflated beyond expected amounts, and event ordering may be non-deterministic when events from different streams share timestamps.

## Expected Correct Output

When functioning correctly, the engine should:
- Accept all four event types through the filter (55 events total, 0 rejected)
- Process events in batches of 10 (producing 6 batches for 55 events)
- Apply `replace` mode so batch snapshots overwrite projection state
- Sort events by `(timestamp, _stream_id, seq)` for deterministic replay
- Produce 4 aggregate projections with accurate quantities and amounts

## Output Schema

### /app/runtime/output/projections.json

Array of projection objects sorted by `aggregate_id`:

| Field | Type | Description |
|-------|------|-------------|
| `aggregate_id` | string | Unique aggregate identifier (e.g., "agg_001") |
| `quantity` | integer | Current quantity from last batch snapshot |
| `total_amount` | float | Current monetary total from last batch snapshot |
| `event_count` | integer | Total number of events processed for this aggregate |
| `last_updated` | string | ISO 8601 timestamp of the most recent event |
| `streams_seen` | array | Sorted list of source stream identifiers |

### /app/runtime/output/replay_summary.json

| Field | Type | Description |
|-------|------|-------------|
| `total_ingested` | integer | Count of all events read from stream files |
| `total_filtered` | integer | Count of events after type filtering |
| `total_rejected` | integer | Count of events rejected by type filter |
| `total_processed` | integer | Count of events processed in projection building |
| `batch_count` | integer | Number of batches executed |
| `batch_size_used` | integer | Batch size configuration value used |
| `projection_count` | integer | Number of unique aggregates with projections |
| `accumulation_mode` | string | Snapshot application mode from config |
| `event_ordering` | string | Description of sort key used ("timestamp_stream_seq") |

## Key Files

| File | Purpose |
|------|---------|
| `/app/runtime/run_engine.py` | Main entry point orchestrating all stages |
| `/app/runtime/config_loader.py` | Reads settings.ini and exposes typed configuration |
| `/app/runtime/stream_reader.py` | Reads JSONL event files and annotates with stream IDs |
| `/app/runtime/event_filter.py` | Filters events by accepted types |
| `/app/runtime/event_sorter.py` | Sorts events into deterministic replay order |
| `/app/runtime/batch_processor.py` | Divides events into fixed-size batch windows |
| `/app/runtime/projection_builder.py` | Replays batched events to build aggregate state |
| `/app/runtime/report_writer.py` | Writes output JSON files |
| `/app/runtime/validators/integrity_check.py` | Post-replay validation checks |
| `/app/runtime/config/settings.ini` | Configuration with multiple sections |

## Your Task

Identify and fix defects in the runtime source files so that the engine produces correct projections and summary output. The bugs involve interactions between configuration parsing, event ordering, batch sizing, and projection state management across multiple modules.
