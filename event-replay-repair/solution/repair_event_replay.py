#!/usr/bin/env python3
"""Repair script for the CQRS event replay engine.

Patches five interacting bugs across multiple modules:
1. Config filter parsing doesn't strip whitespace from comma-separated types
2. Batch size read from wrong config section ([replay] instead of [replay.engine])
3. Projection snapshot application ignores accumulation_mode config
4. Event sorter missing _stream_id in sort key for deterministic ordering
5. ProjectionBuilder doesn't receive accumulation mode from batch processor
"""
import os
import sys


def patch_config_loader():
    """Fix Bug 1: strip whitespace from accepted_types split.
    Fix Bug 2: read batch_size from replay.engine section.
    """
    path = "/app/runtime/config_loader.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug 1: add strip to the split items in _parse_filter_config
    content = content.replace(
        'self._accepted_types = set(raw_types.split(","))',
        'self._accepted_types = set(t.strip() for t in raw_types.split(","))'
    )

    # Bug 2: read batch_size from replay.engine instead of replay
    content = content.replace(
        'return self._config.getint("replay", "batch_size")',
        'return self._config.getint("replay.engine", "batch_size")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_projection_builder():
    """Fix Bug 3: implement accumulation_mode logic in snapshot application.
    Fix Bug 5: accept and use mode from batch processor.
    """
    path = "/app/runtime/projection_builder.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix: ProjectionBuilder should use the processor's mode
    content = content.replace(
        """    def _apply_snapshot(self, snapshot):
        \"\"\"Apply batch snapshot values to running projection state.

        Mode 'replace': snapshot values overwrite projection state
        Mode 'accumulate': snapshot values add to projection state
        \"\"\"
        for agg_id, snap_values in snapshot.items():
            proj = self._projections[agg_id]
            # Apply based on configured mode
            proj["quantity"] += snap_values["quantity"]
            proj["total_amount"] += snap_values["total_amount"]""",
        """    def _apply_snapshot(self, snapshot):
        \"\"\"Apply batch snapshot values to running projection state.

        Mode 'replace': snapshot values overwrite projection state
        Mode 'accumulate': snapshot values add to projection state
        \"\"\"
        mode = self._processor.mode
        for agg_id, snap_values in snapshot.items():
            proj = self._projections[agg_id]
            if mode == "replace":
                proj["quantity"] = snap_values["quantity"]
                proj["total_amount"] = snap_values["total_amount"]
            else:
                proj["quantity"] += snap_values["quantity"]
                proj["total_amount"] += snap_values["total_amount"]"""
    )

    with open(path, "w") as f:
        f.write(content)


def patch_event_sorter():
    """Fix Bug 4: add _stream_id to sort key for deterministic ordering."""
    path = "/app/runtime/event_sorter.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'key=lambda e: (e["timestamp"], e["seq"])',
        'key=lambda e: (e["timestamp"], e["_stream_id"], e["seq"])'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_config_loader()
    patch_projection_builder()
    patch_event_sorter()

    # Re-run engine with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_engine import main as run_main
    run_main()


if __name__ == "__main__":
    main()
