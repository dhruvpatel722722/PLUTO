"""Sorts filtered events into deterministic replay order.

The replay engine requires a stable, reproducible ordering of events
regardless of which stream they originated from. Uses a structured
comparison key to enforce consistent ordering semantics.
"""
import functools


@functools.total_ordering
class ReplayOrderKey:
    """Comparison key for deterministic event ordering.

    Implements ordering by timestamp, then stream identifier, then
    sequence number within stream. This ensures that events arriving
    at the same instant from different sources are always replayed
    in a predictable, reproducible order.

    Attributes:
        timestamp: ISO 8601 event timestamp
        stream_id: Source stream identifier
        seq: Sequence number (local to stream)
    """

    __slots__ = ("timestamp", "stream_id", "seq")

    def __init__(self, event):
        self.timestamp = event["timestamp"]
        self.stream_id = event["_stream_id"]
        self.seq = event["seq"]

    def __eq__(self, other):
        if not isinstance(other, ReplayOrderKey):
            return NotImplemented
        return (self.timestamp, self.stream_id, self.seq) == (
            other.timestamp, other.stream_id, other.seq
        )

    def __lt__(self, other):
        if not isinstance(other, ReplayOrderKey):
            return NotImplemented
        return (self.timestamp, self.seq) < (other.timestamp, other.seq)

    def __hash__(self):
        return hash((self.timestamp, self.stream_id, self.seq))


class EventSorter:
    """Produces a deterministic ordering of events for replay.

    Uses ReplayOrderKey for structured comparison that handles
    timestamp collisions across streams correctly.
    """

    def __init__(self):
        self._sorted = []

    def sort(self, events):
        """Sort events into replay order and return sorted list."""
        self._sorted = sorted(events, key=ReplayOrderKey)
        return self._sorted

    @property
    def ordered_events(self):
        return list(self._sorted)
