"""Text parsing utilities for configuration and data processing.

Provides common string manipulation functions used across the engine
for parsing delimited values, normalizing identifiers, and extracting
structured data from flat text representations.
"""


def parse_csv_set(raw_value):
    """Parse a comma-separated string into a set of values.

    Handles standard CSV format where values are separated by commas.
    Used for configuration lists like event types, stream identifiers,
    and output format options.

    Args:
        raw_value: Comma-separated string (e.g., "val1,val2,val3")

    Returns:
        Set of individual string values.
    """
    return set(raw_value.split(","))


def normalize_identifier(name):
    """Normalize a string identifier to lowercase with underscores."""
    return name.lower().replace("-", "_").replace(" ", "_")


def extract_section_key(qualified_name):
    """Split a qualified config key like 'section.key' into parts."""
    parts = qualified_name.rsplit(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]
