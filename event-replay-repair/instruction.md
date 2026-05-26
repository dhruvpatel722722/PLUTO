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

1. **Stream Reading** — Reads all `.jsonl` files from the data directory, annotating each event with its source stream identifier.

2. **Event Filtering** — Applies configured acceptance rules to retain only recognized event types. All four types (order_placed, payment_received, inventory_adjusted, shipment_dispatched) should pass through.

3. **Deterministic Sorting** — Orders all filtered events for reproducible replay. The ordering must be stable and deterministic even when events from different streams share timestamps.

4. **Batch Projection** — Replays events in fixed-size batch windows to build aggregate state. Within each batch, the last event value per aggregate determines the batch snapshot. Snapshots are then applied to running projection state.

5. **Report Generation** — Writes output projections and replay summary to JSON files.

## Problem

The engine runs without errors but produces incorrect output. Multiple interacting defects cause events to be silently dropped, batch boundaries to be wrong, and projection values to be computed incorrectly. The symptoms include:

- Fewer events passing the filter than expected
- Wrong number of processing batches
- Inflated or incorrect aggregate quantities and monetary totals
- Some events never reaching the projection stage

## Expected Correct Output

When functioning correctly, the engine should:
- Process all 55 events from 3 source streams (0 rejected)
- Divide events into 6 batches of size 10 (with the last batch having 5 events)
- Apply snapshot-replace semantics (each batch overwrites, not accumulates)
- Produce 4 aggregate projections with deterministic values

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
| `/app/runtime/batch_processor.py` | Divides events into batch windows for processing |
| `/app/runtime/projection_builder.py` | Replays batched events to build aggregate state |
| `/app/runtime/report_writer.py` | Writes output JSON files |
| `/app/runtime/validators/integrity_check.py` | Post-replay validation checks |
| `/app/runtime/utils/text_parser.py` | String parsing utilities for config values |
| `/app/runtime/config/settings.ini` | Multi-section configuration file |

## Your Task

Identify and fix defects in the runtime source files so that the engine produces correct projections and summary output. The bugs involve interactions between multiple modules and require tracing data flow through the processing stages.
