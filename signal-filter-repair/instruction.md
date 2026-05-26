# Signal Filter Engine — Debugging Task

## Overview

A multi-channel signal processing engine ingests time-series sensor data from multiple channels, segments it into overlapping analysis windows, applies bandpass filtering, and detects anomalous signal regions using energy-based thresholding. The system produces a list of detected anomaly intervals and processing statistics.

## System Environment

- **Language**: Python 3.11
- **Runtime**: `/app/runtime/` (source, config, data, output)
- **Global system-wide tooling**: `uv` and `pytest` are available
- **Configuration**: `/app/runtime/config/settings.ini`
- **Data**: `/app/runtime/data/` (per-channel JSONL signal files)
- **Output**: `/app/runtime/output/` (detection results and summary)

## Processing Stages

1. **Channel Acquisition** — Reads all `.jsonl` sensor files from the data directory. Each file represents a distinct channel (north, south, east, west).

2. **Channel Selection** — Retains only channels listed in the active configuration. All four channels should be selected for processing.

3. **Windowing** — Segments each channel's sample stream into fixed-size overlapping windows. The normalization mode determines whether windows are scaled before further processing.

4. **Bandpass Filtering** — Applies a frequency-selective filter to each window, attenuating signal components outside the configured passband.

5. **Anomaly Detection** — Computes per-window energy after filtering, establishes a statistical baseline using the configured aggregation method, and flags windows that exceed the baseline by a configurable sigma threshold. Flagged windows are converted to time intervals, merged if close together, and filtered by minimum duration.

6. **Output Generation** — Writes detection results and processing summary.

## Problem

The engine runs without errors but produces incorrect results. Fewer channels are being processed than expected, detection parameters are wrong, and the normalization is destroying the energy information needed for anomaly detection. Multiple interacting defects prevent any anomalies from being detected.

## Expected Correct Output

- All 4 channels selected (1024 total samples, 0 rejected)
- 28 total windows (7 per channel with window_size=64, overlap=0.5)
- Normalization mode: `none` (preserves energy for detection)
- Threshold sigma: 1.5, merge window: 25ms
- 4 raw flags, 3 merged detections across east, north, and west channels

## Output Schema

### /app/runtime/output/detections.json

Array of detection objects sorted chronologically:

| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Source channel identifier |
| `start_ms` | float | Detection start time in milliseconds |
| `end_ms` | float | Detection end time in milliseconds |
| `duration_ms` | float | Detection duration in milliseconds |

### /app/runtime/output/processing_summary.json

| Field | Type | Description |
|-------|------|-------------|
| `total_samples_read` | integer | Total samples across all channel files |
| `channels_available` | array | All channel IDs found in data directory |
| `channels_selected` | array | Channels that passed selection filter |
| `channels_rejected` | array | Channels not matching active config |
| `total_windows` | integer | Total analysis windows created |
| `total_filtered_windows` | integer | Windows processed by bandpass filter |
| `raw_flags` | integer | Windows exceeding energy threshold |
| `detection_count` | integer | Final merged detection count |
| `processing_config` | object | Active configuration parameters |

## Key Files

| File | Purpose |
|------|---------|
| `/app/runtime/run_engine.py` | Main orchestration entry point |
| `/app/runtime/utils/config_reader.py` | Configuration loading with section hierarchy |
| `/app/runtime/utils/array_ops.py` | Array manipulation and windowing utilities |
| `/app/runtime/core/channel_reader.py` | JSONL channel data reader |
| `/app/runtime/core/bandpass.py` | DFT-based bandpass filter |
| `/app/runtime/stages/windowing.py` | Window segmentation and normalization |
| `/app/runtime/stages/filtering.py` | Bandpass filter application |
| `/app/runtime/stages/detection.py` | Energy-based anomaly detection |
| `/app/runtime/validators/signal_check.py` | Output validation |
| `/app/runtime/config/settings.ini` | Multi-section configuration |

## Your Task

Identify and fix defects in the runtime source files so that the engine correctly detects signal anomalies. The bugs involve configuration section resolution, string parsing, normalization mode selection, and sort key completeness across multiple modules.
