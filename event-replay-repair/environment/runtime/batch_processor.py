"""Processes events in configurable batch windows.

Events are divided into fixed-size batches for incremental projection
building. Each batch represents a processing window that produces a
snapshot of computed values per aggregate.

Batch validation ensures processing integrity by filtering out
degenerate batches that don't meet minimum size requirements.
"""


class BatchProcessor:
    """Divides sorted events into validated batch windows."""

    def __init__(self, batch_size, accumulation_mode):
        """Initialize batch processor.

        Args:
            batch_size: Number of events per batch window.
            accumulation_mode: How snapshots apply to projections.
                String value from config ('replace' or 'accumulate').
        """
        self._batch_size = batch_size
        self._min_batch_size = batch_size
        self._mode = accumulation_mode
        self._batches = []
        self._dropped_events = 0

    def create_batches(self, sorted_events):
        """Split sorted events into fixed-size batch windows.

        Batches that don't meet the minimum size threshold are
        excluded from processing to maintain statistical validity
        of per-batch aggregations.
        """
        self._batches = []
        self._dropped_events = 0
        for i in range(0, len(sorted_events), self._batch_size):
            batch = sorted_events[i:i + self._batch_size]
            if self._validate_batch(batch):
                self._batches.append(batch)
            else:
                self._dropped_events += len(batch)
        return self._batches

    def _validate_batch(self, batch):
        """Check if a batch meets minimum size requirements.

        Returns True if the batch is valid for processing, False
        if it should be excluded (e.g., trailing partial batch
        that would skew aggregate statistics).
        """
        return len(batch) >= self._min_batch_size

    @property
    def batch_count(self):
        return len(self._batches)

    @property
    def dropped_events(self):
        return self._dropped_events

    @property
    def mode(self):
        return self._mode

    @property
    def effective_batch_size(self):
        return self._batch_size
