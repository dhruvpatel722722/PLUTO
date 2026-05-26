# CQRS Event Replay Engine — Debugging Task

## Overview

A CQRS (Command Query Responsibility Segregation) event replay engine ingests domain events from multiple source streams, merges and orders them deterministically, then replays them in configurable batches to rebuild aggregate state projections. The system processes order, payment, inventory, and shipment events to produce materialized views for downstream consumers.

## System Environment

- **Language**: Python 3.11
- **Runtime**: `/app/runtime/` (source, config, data, output)
- **Global system-wide tooling**: `uv` and `pytest` are available
- **Configuration**: `/app/runtime/config/settings.ini`
- **Data**: `/app/runtime/data/` (JSONL event streams)
- **Output**: `/app/runtime/output/` (JSON projection and summary files)

## Processing Stages

1. **Ingestion** — Reads all `.jsonl` files from `/app/runtime/data/`, annotating each event with its source stream identifier. Events are read from `inventory_stream.jsonl`, `orders_stream.jsonl`, and `payments_stream.jsonl`.

2. **Filtering** — Applies the `accepted_event_types` configuration to retain only recognized event types. The accepted types are: `order_placed`, `payment_received`, `inventory_adjusted`, and `shipment_dispatched`.

3. **Sorting** — Orders all filtered events deterministically for replay. The correct ordering uses `timestamp` as primary key, then `_stream_id` (source file) as secondary key, then `seq` (sequence within each stream) as tertiary key. This ensures reproducible replay even when events share the same timestamp across different streams.

4. **Projection Building** — Replays events in fixed-size batches (configured in the `[replay.projection]` section) to build aggregate state. Each batch produces a snapshot; the final snapshot values for each aggregate within a batch become that aggregate's current quantity and total_amount. Event counts accumulate normally across batches.

5. **Report Generation** — Writes `/app/runtime/output/projections.json` (list of aggregate projections) and `/app/runtime/output/replay_summary.json` (processing statistics).

## Problem

The engine runs without crashing but produces incorrect output. Some event types that should be included are missing from projections, the batch sizes appear wrong, aggregate quantities and totals are inflated, and the event ordering is non-deterministic when events arrive at the same timestamp from different source streams.

## Expected Correct Output

When functioning correctly, the engine should:
- Include all four event types (`order_placed`, `payment_received`, `inventory_adjusted`, `shipment_dispatched`) in processing
- Use the projection-specific batch size of 10 events per batch
- Compute projections where each batch's final snapshot values replace (not accumulate onto) the previous projection state for quantity and total_amount
- Produce deterministic ordering by sorting on `(timestamp, _stream_id, seq)`

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

### /app/runtime/output/replay_summary.json

| Field | Type | Description |
|-------|------|-------------|
| `total_ingested` | integer | Count of all events read from stream files |
| `total_filtered` | integer | Count of events after type filtering |
| `total_processed` | integer | Count of events processed in projection building |
| `batch_count` | integer | Number of batches executed |
| `projection_count` | integer | Number of unique aggregates with projections |
| `event_ordering` | string | Description of sort key used ("timestamp_stream_seq") |

## Key Files

| File | Purpose |
|------|---------|
| `/app/runtime/config_loader.py` | Reads settings.ini and exposes configuration properties |
| `/app/runtime/event_ingestor.py` | Ingests JSONL streams and filters by event type |
| `/app/runtime/event_sorter.py` | Sorts events into deterministic replay order |
| `/app/runtime/projection_builder.py` | Replays events in batches to build aggregate projections |
| `/app/runtime/report_writer.py` | Writes output JSON files |
| `/app/runtime/run_engine.py` | Main entry point orchestrating all stages |
| `/app/runtime/config/settings.ini` | Configuration with section-based parameters |

## Your Task

Identify and fix defects in the runtime source files so that the engine produces correct projections and summary output. The bugs span multiple files and involve configuration parsing, event ordering logic, and projection state management.
