"""Main entry point for the multi-channel signal processing engine.

Orchestrates the processing stages:
1. Channel acquisition - read signal data from JSONL files
2. Channel selection - retain only configured channels
3. Windowing - segment into overlapping analysis frames
4. Filtering - apply bandpass filter to each window
5. Detection - identify anomalous signal regions
6. Output - write detections and processing summary

Usage: python3 -m runtime.run_engine
"""
from runtime.utils.config_reader import SignalConfig
from runtime.core.channel_reader import ChannelReader
from runtime.stages.windowing import WindowingStage
from runtime.stages.filtering import FilteringStage
from runtime.stages.detection import DetectionStage
from runtime.validators.signal_check import SignalChecker
import json
import os


def main():
    """Execute the full signal processing chain."""
    config = SignalConfig()

    # Stage 1: Read all channel data
    reader = ChannelReader(config.data_directory)
    reader.read_all()

    # Stage 2: Select configured channels only
    active_channels = config.channels
    selected_data = {}
    for ch_id in reader.channel_ids:
        if ch_id in active_channels:
            selected_data[ch_id] = reader.get_channel(ch_id)

    # Stage 3: Window and normalize
    windower = WindowingStage(config)
    windowed = windower.process(selected_data)

    # Stage 4: Apply bandpass filter
    filterer = FilteringStage(config)
    filtered = filterer.process(windowed)

    # Stage 5: Detect anomalies
    detector = DetectionStage(config)
    detections = detector.process(filtered)

    # Stage 6: Write output
    output_dir = config.output_directory
    os.makedirs(output_dir, exist_ok=True)

    # Write detections
    detections_path = os.path.join(output_dir, config.detections_file)
    with open(detections_path, "w") as f:
        json.dump(detections, f, indent=2)

    # Write summary
    summary = {
        "total_samples_read": reader.total_samples,
        "channels_available": reader.channel_ids,
        "channels_selected": sorted(selected_data.keys()),
        "channels_rejected": sorted(
            set(reader.channel_ids) - set(selected_data.keys())
        ),
        "total_windows": windower.total_windows,
        "window_counts_per_channel": windower.channel_window_counts,
        "total_filtered_windows": filterer.total_filtered,
        "raw_flags": detector.raw_flags,
        "detection_count": detector.detection_count,
        "processing_config": {
            "sample_rate": config.sample_rate,
            "window_size": config.window_size,
            "overlap_ratio": config.overlap_ratio,
            "normalization": config.normalization_mode,
            "filter_type": config.filter_type,
            "filter_band": [config.filter_low_cutoff, config.filter_high_cutoff],
            "filter_order": config.filter_order,
            "threshold_sigma": config.get_detector_param("threshold_sigma", float),
            "merge_window_ms": config.merge_window_ms,
            "min_duration_ms": config.min_duration_ms,
        },
    }

    summary_path = os.path.join(output_dir, config.summary_file)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Validate
    checker = SignalChecker(detections, summary)
    checker.validate()

    return detections, summary


if __name__ == "__main__":
    main()
