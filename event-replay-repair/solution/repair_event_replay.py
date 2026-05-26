#!/usr/bin/env python3
"""Repair script for the CQRS event replay engine.

Patches four bugs:
1. Config space in accepted_event_types comma-split (config_loader.py)
2. Wrong config section for batch_size (config_loader.py)
3. Snapshot accumulation instead of replacement (projection_builder.py)
4. Missing _stream_id in sort key (event_sorter.py)
"""
import os
import sys


def patch_config_loader():
    """Fix Bug A: strip whitespace from comma-split event types.
    Fix Bug B: read batch_size from replay.projection section.
    """
    path = "/app/runtime/config_loader.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug A: add .strip() to split items
    content = content.replace(
        'return set(raw.split(","))',
        'return set(item.strip() for item in raw.split(","))'
    )

    # Bug B: read batch_size from replay.projection instead of replay
    content = content.replace(
        'return self._config.getint("replay", "batch_size")',
        'return self._config.getint("replay.projection", "batch_size")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_projection_builder():
    """Fix Bug C: replace snapshot accumulation with last-write-wins."""
    path = "/app/runtime/projection_builder.py"
    with open(path, "r") as f:
        content = f.read()

    # Change += to = for snapshot application
    content = content.replace(
        'self._projections[agg_id]["quantity"] += snap["quantity"]',
        'self._projections[agg_id]["quantity"] = snap["quantity"]'
    )
    content = content.replace(
        'self._projections[agg_id]["total_amount"] += snap["total_amount"]',
        'self._projections[agg_id]["total_amount"] = snap["total_amount"]'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_event_sorter():
    """Fix Bug D: add _stream_id to sort key for deterministic ordering."""
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

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_engine import main as run_main
    run_main()


if __name__ == "__main__":
    main()
