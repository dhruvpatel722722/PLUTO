"""Reads raw event streams from JSONL data files.

Each file represents a distinct event source (stream). Events are annotated
with their originating stream identifier for downstream processing.

Implementation note: seq values are stream-local, not globally unique
across streams. Two events from different streams may share the same seq.
"""
import json
import os


class StreamReader:
    """Low-level reader for JSONL event stream files.

    Reads all .jsonl files from a configured directory and produces
    a flat list of event dictionaries annotated with source metadata.
    """

    def __init__(self, data_directory):
        self._data_dir = data_directory
        self._raw_events = []

    def read_all(self):
        """Read all .jsonl files from the data directory.

        Files are processed in sorted order. Each event is annotated with
        a _stream_id derived from the filename (without extension).
        """
        for filename in sorted(os.listdir(self._data_dir)):
            if not filename.endswith(".jsonl"):
                continue
            filepath = os.path.join(self._data_dir, filename)
            stream_id = filename.replace(".jsonl", "")
            with open(filepath, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    event["_stream_id"] = stream_id
                    event["_source_line"] = line_num
                    self._raw_events.append(event)
        return self

    @property
    def events(self):
        """Return all raw events read from streams."""
        return list(self._raw_events)

    @property
    def count(self):
        return len(self._raw_events)
