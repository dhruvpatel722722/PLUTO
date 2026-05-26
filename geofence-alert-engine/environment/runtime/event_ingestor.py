"""Event ingestion from sensor data files."""
import json
import os
from datetime import datetime


class EventIngestor:
    """Reads and filters location events from sensor feed files."""

    def __init__(self, config, data_dir=None):
        self._config = config
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        self._data_dir = data_dir

    def ingest_all(self):
        """Read all events from active sensor feeds and return sorted list."""
        all_events = []
        for filename in os.listdir(self._data_dir):
            if not filename.endswith(".jsonl"):
                continue
            feed_name = filename.replace(".jsonl", "")
            if feed_name not in self._config.active_feeds:
                continue
            filepath = os.path.join(self._data_dir, filename)
            events = self._read_feed(filepath, feed_name)
            all_events.extend(events)

        # Sort events by timestamp then sequence for deterministic processing
        all_events.sort(key=lambda e: (e["timestamp"], e["seq"]))
        return all_events

    def _read_feed(self, filepath, feed_name):
        """Parse a single JSONL feed file into event dicts."""
        events = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                event = {
                    "timestamp": datetime.fromisoformat(raw["ts"]),
                    "sensor_id": raw["sensor_id"],
                    "seq": raw["seq"],
                    "lat": raw["lat"],
                    "lon": raw["lon"],
                    "asset_id": raw["asset_id"],
                    "feed": feed_name,
                }
                events.append(event)
        return events
