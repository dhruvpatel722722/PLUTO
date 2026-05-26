"""Post-replay integrity validation.

Verifies that projections satisfy basic invariants after replay completes.
This module runs after projection building to detect data anomalies
that might indicate processing errors.
"""


class IntegrityChecker:
    """Validates projection integrity after replay completion.

    Checks event conservation (sum of per-aggregate counts matches
    total processed) and stream coverage (each aggregate has seen
    at least one source stream).
    """

    def __init__(self, projections, summary):
        self._projections = projections
        self._summary = summary
        self._violations = []

    def check_event_conservation(self):
        """Verify total events processed matches sum of per-aggregate counts."""
        total_from_projections = sum(p["event_count"] for p in self._projections)
        if total_from_projections != self._summary["total_processed"]:
            self._violations.append(
                f"Event conservation violated: projection sum "
                f"{total_from_projections} != processed {self._summary['total_processed']}"
            )
        return self

    def check_stream_coverage(self):
        """Verify each aggregate has seen at least one stream."""
        for proj in self._projections:
            if not proj.get("streams_seen"):
                self._violations.append(
                    f"Aggregate {proj['aggregate_id']} has no streams_seen"
                )
        return self

    @property
    def is_valid(self):
        return len(self._violations) == 0

    @property
    def violations(self):
        return list(self._violations)
