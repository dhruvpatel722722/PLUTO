"""Builds aggregate projections from ordered event stream."""
import json


class ProjectionBuilder:
    """Replays events in batches to build aggregate state projections.

    Each aggregate (identified by aggregate_id) accumulates state from events.
    Projections track quantities, totals, and event counts per aggregate.
    """

    def __init__(self, config):
        self._config = config
        self._projections = {}
        self._batch_count = 0
        self._events_processed = 0

    def replay(self, sorted_events):
        """Replay all events in batches to build projections."""
        batch_size = self._config.batch_size
        for i in range(0, len(sorted_events), batch_size):
            batch = sorted_events[i:i + batch_size]
            self._process_batch(batch)
            self._batch_count += 1
        return self

    def _process_batch(self, batch):
        """Process a single batch of events, updating projections."""
        snapshot = {}
        for event in batch:
            agg_id = event["aggregate_id"]
            if agg_id not in self._projections:
                self._projections[agg_id] = {
                    "aggregate_id": agg_id,
                    "quantity": 0,
                    "total_amount": 0.0,
                    "event_count": 0,
                    "last_updated": None,
                }
            if agg_id not in snapshot:
                snapshot[agg_id] = {
                    "quantity": 0,
                    "total_amount": 0.0,
                }

            qty = event.get("quantity", 0)
            amount = event.get("amount", 0.0)

            snapshot[agg_id]["quantity"] = qty
            snapshot[agg_id]["total_amount"] = amount

            self._projections[agg_id]["event_count"] += 1
            self._projections[agg_id]["last_updated"] = event["timestamp"]
            self._events_processed += 1

        # Apply batch snapshot to projections
        for agg_id, snap in snapshot.items():
            self._projections[agg_id]["quantity"] += snap["quantity"]
            self._projections[agg_id]["total_amount"] += snap["total_amount"]

    def get_projections(self):
        """Return all projections sorted by aggregate_id."""
        return sorted(
            self._projections.values(),
            key=lambda p: p["aggregate_id"]
        )

    @property
    def batch_count(self):
        return self._batch_count

    @property
    def events_processed(self):
        return self._events_processed
