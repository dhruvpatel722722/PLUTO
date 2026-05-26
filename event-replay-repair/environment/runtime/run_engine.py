"""Main entry point for the CQRS event replay engine."""
from runtime.config_loader import ReplayConfig
from runtime.event_ingestor import EventIngestor
from runtime.event_sorter import EventSorter
from runtime.projection_builder import ProjectionBuilder
from runtime.report_writer import ReportWriter


def main():
    """Execute the full event replay process."""
    config = ReplayConfig()

    # Stage 1: Ingest events from all stream files
    ingestor = EventIngestor(config)
    ingestor.ingest()

    # Stage 2: Filter events by accepted types
    filtered_events = ingestor.get_filtered_events()

    # Stage 3: Sort events into deterministic replay order
    sorter = EventSorter()
    sorted_events = sorter.sort(filtered_events)

    # Stage 4: Build projections by replaying events in batches
    builder = ProjectionBuilder(config)
    builder.replay(sorted_events)

    # Stage 5: Write output files
    writer = ReportWriter(config)
    projections = builder.get_projections()
    writer.write_projections(projections)

    summary = {
        "total_ingested": ingestor.total_ingested,
        "total_filtered": len(filtered_events),
        "total_processed": builder.events_processed,
        "batch_count": builder.batch_count,
        "projection_count": len(projections),
        "event_ordering": "timestamp_stream_seq",
    }
    writer.write_summary(summary)


if __name__ == "__main__":
    main()
