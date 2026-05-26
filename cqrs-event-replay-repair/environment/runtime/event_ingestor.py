"""Ingests events from multiple stream files and produces a unified event log."""
import json
import os


class EventIngestor:
    """Reads JSONL event streams and merges them into a single ordered sequence."""

    def __init__(self, config):
        self._config = config
        self._events = []

    def ingest(self):
        """Read all stream files from the data directory."""
        data_dir = self._config.data_directory
        for filename in sorted(os.listdir(data_dir)):
            if not filename.endswith(".jsonl"):
                continue
            filepath = os.path.join(data_dir, filename)
            stream_id = filename.replace(".jsonl", "")
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    event["_stream_id"] = stream_id
                    self._events.append(event)
        return self

    def get_filtered_events(self):
        """Return events filtered by accepted event types from config."""
        accepted = self._config.accepted_event_types
        return [e for e in self._events if e.get("event_type") in accepted]

    def get_all_events(self):
        """Return all ingested events unfiltered."""
        return list(self._events)

    @property
    def total_ingested(self):
        return len(self._events)
