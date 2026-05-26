"""Processes events in configurable batch windows.

Events are divided into fixed-size batches. Each batch produces a snapshot
of computed values per aggregate. The snapshot application mode determines
how batch results merge into the running projection state.
"""


class BatchProcessor:
    """Divides sorted events into batches and processes each batch."""

    def __init__(self, batch_size, accumulation_mode):
        """Initialize batch processor.

        Args:
            batch_size: Number of events per batch window.
            accumulation_mode: How snapshots apply - 'replace' means
                last-write-wins, 'accumulate' means running sum.
        """
        self._batch_size = batch_size
        self._mode = accumulation_mode
        self._batches = []

    def create_batches(self, sorted_events):
        """Split sorted events into fixed-size batch windows."""
        self._batches = []
        for i in range(0, len(sorted_events), self._batch_size):
            batch = sorted_events[i:i + self._batch_size]
            self._batches.append(batch)
        return self._batches

    @property
    def batch_count(self):
        return len(self._batches)

    @property
    def mode(self):
        return self._mode
