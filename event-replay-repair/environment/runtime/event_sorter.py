"""Sorts filtered events into deterministic replay order.

The replay engine requires a stable, reproducible ordering of events
regardless of which stream they originated from. Events are ordered by
their timestamp, with ties broken by sequence number within each stream.
Note: seq is local to each stream, not globally unique across streams.
"""


class EventSorter:
    """Produces a deterministic ordering of events for replay.

    Sort priority:
      1. timestamp (chronological order)
      2. seq (sequence within stream)

    This ensures reproducible replay across runs.
    """

    def __init__(self):
        self._sorted = []

    def sort(self, events):
        """Sort events into replay order and return sorted list."""
        self._sorted = sorted(
            events,
            key=lambda e: (e["timestamp"], e["seq"])
        )
        return self._sorted

    @property
    def ordered_events(self):
        return list(self._sorted)
