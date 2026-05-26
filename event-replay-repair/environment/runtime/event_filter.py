"""Filters events based on configured acceptance rules.

Only events whose event_type exactly matches an entry in the accepted
set will pass through to the sorting and projection stages. Events
that do not match are counted as rejected for audit purposes.
"""


class EventFilter:
    """Applies type-based filtering to raw event streams."""

    def __init__(self, accepted_types):
        """Initialize with set of accepted event type strings.

        Args:
            accepted_types: Set of string event type names that should
                be retained. Matching is exact (case-sensitive).
        """
        self._accepted = accepted_types
        self._passed = []
        self._rejected = []

    def apply(self, events):
        """Filter events, separating accepted from rejected.

        Each event's 'event_type' field is checked against the accepted
        set. Events without an event_type field are always rejected.
        """
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
