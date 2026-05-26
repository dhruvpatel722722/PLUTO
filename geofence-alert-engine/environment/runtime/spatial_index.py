"""Spatial grid indexing for geofence zone containment checks."""


class SpatialIndex:
    """Maps location events to geofence zones using bounding-box containment."""

    def __init__(self, zones):
        self._zones = zones

    def find_zone(self, lat, lon):
        """Return the zone ID containing the given coordinates, or None."""
        for zone_id, bounds in self._zones.items():
            if (bounds["lat_min"] <= lat <= bounds["lat_max"] and
                    bounds["lon_min"] <= lon <= bounds["lon_max"]):
                return zone_id
        return None

    def classify_events(self, events):
        """Add zone_id field to each event based on spatial containment."""
        for event in events:
            zone = self.find_zone(event["lat"], event["lon"])
            event["zone_id"] = zone
        return events
