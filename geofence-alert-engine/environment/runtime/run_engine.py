"""Main entry point for the geofence alert engine."""
from runtime.config_loader import ConfigLoader
from runtime.event_ingestor import EventIngestor
from runtime.spatial_index import SpatialIndex
from runtime.dwell_tracker import DwellTracker
from runtime.alert_generator import AlertGenerator
from runtime.report_writer import ReportWriter


def main():
    """Execute the full geofence alert processing workflow."""
    # Load configuration
    config = ConfigLoader()

    # Ingest events from active sensor feeds
    ingestor = EventIngestor(config)
    events = ingestor.ingest_all()

    # Classify events into geofence zones
    index = SpatialIndex(config.zones)
    events = index.classify_events(events)

    # Compute dwell times per asset/zone
    tracker = DwellTracker(config)
    dwell_times = tracker.compute_dwell_times(events)

    # Generate alerts for threshold violations
    generator = AlertGenerator(config)
    alerts = generator.generate_alerts(dwell_times, events)

    # Write output reports
    writer = ReportWriter()
    writer.write_event_log(events)
    writer.write_dwell_summary(dwell_times)
    writer.write_alerts(alerts)
    writer.write_processing_stats(events, dwell_times, alerts)


if __name__ == "__main__":
    main()
