#!/usr/bin/env python3
"""Repair script for the CQRS event replay engine.

Patches five interacting bugs:
1. text_parser.parse_csv_set doesn't strip whitespace from split values
2. config_loader.get_engine_param reads from wrong section (replay vs replay.engine)
3. projection_builder uses == True instead of == 'replace' for mode check
4. event_sorter ReplayOrderKey.__lt__ doesn't include stream_id in comparison
5. batch_processor._validate_batch drops partial batches (min_batch_size too high)
"""
import os
import sys


def patch_text_parser():
    """Fix Bug A: strip whitespace in parse_csv_set."""
    path = "/app/runtime/utils/text_parser.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'return set(raw_value.split(","))',
        'return set(v.strip() for v in raw_value.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_config_loader():
    """Fix Bug B: get_engine_param should read from replay.engine section."""
    path = "/app/runtime/config_loader.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        '_ENGINE_SECTION = "replay"',
        '_ENGINE_SECTION = "replay.engine"'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_projection_builder():
    """Fix Bug C: mode comparison should check string value, not boolean."""
    path = "/app/runtime/projection_builder.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'if self._mode == True:',
        'if self._mode == "replace":'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_event_sorter():
    """Fix Bug D: include stream_id in sort comparison for determinism."""
    path = "/app/runtime/event_sorter.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'return (self.timestamp, self.seq) < (other.timestamp, other.seq)',
        'return (self.timestamp, self.stream_id, self.seq) < (other.timestamp, other.stream_id, other.seq)'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_batch_processor():
    """Fix Bug E: don't drop partial final batches."""
    path = "/app/runtime/batch_processor.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._min_batch_size = batch_size',
        'self._min_batch_size = 1'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_text_parser()
    patch_config_loader()
    patch_projection_builder()
    patch_event_sorter()
    patch_batch_processor()

    # Re-run engine with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_engine import main as run_main
    run_main()


if __name__ == "__main__":
    main()
