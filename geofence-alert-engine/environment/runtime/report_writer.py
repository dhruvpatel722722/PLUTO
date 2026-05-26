"""Report generation for geofence alert summaries."""
import json
import os


class ReportWriter:
    """Writes structured JSON output reports."""

    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "output")
        self._output_dir = output_dir
        os.makedirs(self._output_dir, exist_ok=True)

    def write_event_log(self, events):
        """Write the processed event log with zone assignments."""
        records = []
        for event in events:
            records.append({
                "timestamp": event["timestamp"].isoformat(),
                "sensor_id": event["sensor_id"],
                "seq": event["seq"],
                "asset_id": event["asset_id"],
                "lat": event["lat"],
                "lon": event["lon"],
                "zone_id": event["zone_id"],
                "feed": event["feed"],
            })

        path = os.path.join(self._output_dir, "event_log.json")
        with open(path, "w") as f:
            json.dump({"events": records, "total_count": len(records)}, f, indent=2)

    def write_dwell_summary(self, dwell_times):
        """Write dwell time summary per asset-zone pair."""
        records = []
        for (asset_id, zone_id), duration in sorted(dwell_times.items()):
            records.append({
                "asset_id": asset_id,
                "zone_id": zone_id,
                "total_dwell_seconds": round(duration, 1),
            })

        path = os.path.join(self._output_dir, "dwell_summary.json")
        with open(path, "w") as f:
            json.dump({"dwell_records": records, "record_count": len(records)}, f, indent=2)

    def write_alerts(self, alerts):
        """Write generated alerts to output."""
        path = os.path.join(self._output_dir, "alerts.json")
        with open(path, "w") as f:
            json.dump({"alerts": alerts, "alert_count": len(alerts)}, f, indent=2)

    def write_processing_stats(self, events, dwell_times, alerts):
        """Write processing statistics summary."""
        feeds_seen = set(e["feed"] for e in events)
        zones_hit = set(e["zone_id"] for e in events if e["zone_id"] is not None)
        assets_seen = set(e["asset_id"] for e in events)

        stats = {
            "total_events_processed": len(events),
            "active_feeds_count": len(feeds_seen),
            "feeds_processed": sorted(feeds_seen),
            "zones_with_activity": sorted(zones_hit),
            "unique_assets": sorted(assets_seen),
            "dwell_records_count": len(dwell_times),
            "alerts_generated": len(alerts),
        }

        path = os.path.join(self._output_dir, "stats.json")
        with open(path, "w") as f:
            json.dump(stats, f, indent=2)
