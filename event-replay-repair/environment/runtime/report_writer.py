"""Writes output files: projections and replay summary.

Generates the final JSON output consumed by downstream systems.
"""
import json
import os


class ReportWriter:
    """Generates output JSON files from replay results."""

    def __init__(self, config):
        self._config = config

    def write_projections(self, projections):
        """Write projections list to output JSON file."""
        output_dir = self._config.output_directory
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, self._config.output_projections_file)
        with open(filepath, "w") as f:
            json.dump(projections, f, indent=2)

    def write_summary(self, summary):
        """Write replay summary to output JSON file."""
        output_dir = self._config.output_directory
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, self._config.output_summary_file)
        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)
