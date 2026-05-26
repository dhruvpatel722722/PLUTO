"""Builds aggregate projections by replaying batched events.

Each aggregate accumulates state from events processed in batch order.
Within each batch, a snapshot captures the final computed values.
After batch processing, snapshots are applied to the running projection
state according to the configured accumulation mode.
"""


class ProjectionBuilder:
    """Replays batched events to build per-aggregate state projections."""

    def __init__(self, batch_processor):
        self._processor = batch_processor
        self._projections = {}
        self._events_processed = 0

    def replay_batches(self, batches):
        """Process all batches, building projection state incrementally."""
        for batch in batches:
            self._process_single_batch(batch)
        return self

    def _process_single_batch(self, batch):
        """Process one batch: compute snapshot then apply to projections."""
        snapshot = {}

        for event in batch:
            agg_id = event["aggregate_id"]

            # Initialize projection if first encounter
            if agg_id not in self._projections:
                self._projections[agg_id] = {
                    "aggregate_id": agg_id,
                    "quantity": 0,
                    "total_amount": 0.0,
                    "event_count": 0,
                    "last_updated": None,
                    "streams_seen": set(),
                }

            # Build batch snapshot - last value per aggregate wins within batch
            if agg_id not in snapshot:
                snapshot[agg_id] = {"quantity": 0, "total_amount": 0.0}

            snapshot[agg_id]["quantity"] = event.get("quantity", 0)
            snapshot[agg_id]["total_amount"] = event.get("amount", 0.0)

            # These always accumulate regardless of mode
            self._projections[agg_id]["event_count"] += 1
            self._projections[agg_id]["last_updated"] = event["timestamp"]
            self._projections[agg_id]["streams_seen"].add(event["_stream_id"])
            self._events_processed += 1

        # Apply batch snapshot to projection state
        self._apply_snapshot(snapshot)

    def _apply_snapshot(self, snapshot):
        """Apply batch snapshot values to running projection state.

        Mode 'replace': snapshot values overwrite projection state
        Mode 'accumulate': snapshot values add to projection state
        """
        for agg_id, snap_values in snapshot.items():
            proj = self._projections[agg_id]
            # Apply based on configured mode
            proj["quantity"] += snap_values["quantity"]
            proj["total_amount"] += snap_values["total_amount"]

    def get_projections(self):
        """Return finalized projections sorted by aggregate_id.

        Converts internal sets to lists for JSON serialization.
        """
        result = []
        for proj in sorted(self._projections.values(), key=lambda p: p["aggregate_id"]):
            entry = {
                "aggregate_id": proj["aggregate_id"],
                "quantity": proj["quantity"],
                "total_amount": round(proj["total_amount"], 2),
                "event_count": proj["event_count"],
                "last_updated": proj["last_updated"],
                "streams_seen": sorted(proj["streams_seen"]),
            }
            result.append(entry)
        return result

    @property
    def events_processed(self):
        return self._events_processed

    @property
    def aggregate_count(self):
        return len(self._projections)
