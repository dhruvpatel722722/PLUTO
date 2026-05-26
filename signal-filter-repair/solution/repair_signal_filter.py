#!/usr/bin/env python3
"""Repair script for the multi-channel signal processing engine.

Patches five interacting bugs:
1. Channel config whitespace: ' west' not stripped in split
2. Normalization reads from [processing] not [processing.window]
3. Detector section constant points to parent 'analysis' not 'analysis.detector'
4. DetectionKey.__lt__ omits channel_id for deterministic ordering
5. merge_window_ms reads via get_detector_param which uses wrong section
"""
import sys


def patch_config_reader():
    """Fix Bug A: strip channel names. Fix Bug C: detector section."""
    path = "/app/runtime/utils/config_reader.py"
    with open(path, "r") as f:
        content = f.read()

    # Bug A: strip whitespace from channel split
    content = content.replace(
        'self._channel_cache = set(raw.split(","))',
        'self._channel_cache = set(ch.strip() for ch in raw.split(","))'
    )

    # Bug B: read normalization from processing.window section
    content = content.replace(
        'return self._config.get("processing", "normalization")',
        'return self._config.get("processing.window", "normalization")'
    )

    # Bug C: detector section should be analysis.detector
    content = content.replace(
        '_DETECTOR_SECTION = "analysis"',
        '_DETECTOR_SECTION = "analysis.detector"'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_detection():
    """Fix Bug D: include channel_id in DetectionKey.__lt__."""
    path = "/app/runtime/stages/detection.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'return (self.start_ms, self.end_ms) < (other.start_ms, other.end_ms)',
        'return (self.start_ms, self.channel_id, self.end_ms) < (other.start_ms, other.channel_id, other.end_ms)'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_config_reader()
    patch_detection()

    # Re-run engine with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_engine import main as run_main
    run_main()


if __name__ == "__main__":
    main()
