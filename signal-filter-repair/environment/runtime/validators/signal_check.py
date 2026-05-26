"""Post-processing validation for signal analysis results.

Performs basic sanity checks on detection output to catch obvious
processing errors before output is consumed downstream.
"""


class SignalChecker:
    """Validates signal processing output integrity."""

    def __init__(self, detections, summary):
        self._detections = detections
        self._summary = summary
        self._issues = []

    def validate(self):
        """Run all validation checks."""
        self._check_detection_ordering()
        self._check_duration_validity()
        return self

    def _check_detection_ordering(self):
        """Verify detections are in chronological order."""
        for i in range(1, len(self._detections)):
            if self._detections[i]["start_ms"] < self._detections[i-1]["start_ms"]:
                self._issues.append("Detections not in chronological order")
                break

    def _check_duration_validity(self):
        """Verify all detections have positive duration."""
        for d in self._detections:
            if d["duration_ms"] <= 0:
                self._issues.append(f"Invalid duration: {d}")
                break

    @property
    def issues(self):
        return list(self._issues)

    @property
    def is_valid(self):
        return len(self._issues) == 0
