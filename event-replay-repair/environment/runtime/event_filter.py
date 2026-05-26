"""Filters events based on configured acceptance rules.

Only events whose event_type is in the accepted set will pass through
to the sorting and projection stages.
"""


class EventFilter:
    """Applies type-based filtering to raw event streams."""

    def __init__(self, accepted_types):
        """Initialize with set of accepted event type strings."""
        self._accepted = accepted_types
        self._passed = []
        self._rejected = []

    def apply(self, events):
        """Filter events, separating accepted from rejected."""
        for event in events:
            etype = event.get("event_type", "")
            if etype in self._accepted:
                self._passed.append(event)
            else:
                self._rejected.append(event)
        return self

    @property
    def passed_events(self):
        return list(self._passed)

    @property
    def rejected_count(self):
        return len(self._rejected)

    @property
    def passed_count(self):
        return len(self._passed)
