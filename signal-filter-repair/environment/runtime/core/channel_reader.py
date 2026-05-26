"""Reads multi-channel signal data from JSONL source files.

Each JSONL file represents a sensor channel. Samples are annotated
with channel identity and line-order position for downstream tracing.
"""
import json
import os


class ChannelReader:
    """Reads signal samples from per-channel JSONL files.

    Each line in a channel file contains a JSON object with:
    - timestamp_ms: sample timestamp in milliseconds
    - value: float amplitude value
    - quality: signal quality indicator (0.0 - 1.0)
    """

    def __init__(self, data_directory):
        self._data_dir = data_directory
        self._channels = {}
        self._total_samples = 0

    def read_all(self):
        """Read all .jsonl channel files from the data directory."""
        for filename in sorted(os.listdir(self._data_dir)):
            if not filename.endswith(".jsonl"):
                continue
            channel_id = filename.replace(".jsonl", "")
            filepath = os.path.join(self._data_dir, filename)
            samples = []
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    record["_channel"] = channel_id
                    samples.append(record)
            self._channels[channel_id] = samples
            self._total_samples += len(samples)
        return self

    @property
    def channel_ids(self):
        """Return sorted list of channel IDs that were read."""
        return sorted(self._channels.keys())

    def get_channel(self, channel_id):
        """Return sample list for a specific channel."""
        return list(self._channels.get(channel_id, []))

    @property
    def all_channels(self):
        """Return dict mapping channel_id to sample list."""
        return dict(self._channels)

    @property
    def total_samples(self):
        return self._total_samples
