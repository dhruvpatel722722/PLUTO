"""Sorts events into deterministic replay order."""


class EventSorter:
    """Produces a deterministic ordering of events for replay.

    Events are sorted by timestamp, then by sequence number within each stream.
    Note: seq is local to each stream, not globally unique.
    """

    def sort(self, events):
        """Sort events for deterministic replay ordering."""
        return sorted(
            events,
            key=lambda e: (e["timestamp"], e["seq"])
        )
