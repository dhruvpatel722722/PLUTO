"""Main entry point for the CQRS event replay engine.

Orchestrates the five processing stages:
1. Stream reading - ingest raw events from JSONL files
2. Filtering - retain only accepted event types
3. Sorting - deterministic ordering for reproducible replay
4. Batch projection - replay events in windows to build state
5. Report generation - write output files

Usage: python3 -m runtime.run_engine
"""
from runtime.config_loader import ReplayConfig
from runtime.stream_reader import StreamReader
from runtime.event_filter import EventFilter
from runtime.event_sorter import EventSorter
from runtime.batch_processor import BatchProcessor
from runtime.projection_builder import ProjectionBuilder
from runtime.report_writer import ReportWriter
from runtime.validators.integrity_check import IntegrityChecker


def main():
    """Execute the full event replay process."""
    config = ReplayConfig()

    # Stage 1: Read raw events from all stream files
    reader = StreamReader(config.data_directory)
    reader.read_all()

    # Stage 2: Filter events by accepted types
    event_filter = EventFilter(config.accepted_event_types)
    event_filter.apply(reader.events)

    # Stage 3: Sort filtered events into deterministic order
    sorter = EventSorter()
    sorted_events = sorter.sort(event_filter.passed_events)

    # Stage 4: Process in batches and build projections
    processor = BatchProcessor(config.batch_size, config.accumulation_mode)
    batches = processor.create_batches(sorted_events)

    builder = ProjectionBuilder(processor)
    builder.replay_batches(batches)

    # Stage 5: Write output
    writer = ReportWriter(config)
    projections = builder.get_projections()
    writer.write_projections(projections)

    summary = {
        "total_ingested": reader.count,
        "total_filtered": event_filter.passed_count,
        "total_rejected": event_filter.rejected_count,
        "total_processed": builder.events_processed,
        "batch_count": processor.batch_count,
        "batch_size_used": config.batch_size,
        "projection_count": builder.aggregate_count,
        "accumulation_mode": config.accumulation_mode,
        "event_ordering": "timestamp_stream_seq",
    }
    writer.write_summary(summary)

    # Post-replay validation
    checker = IntegrityChecker(projections, summary)
    checker.check_event_conservation()
    checker.check_stream_coverage()

    return projections, summary


if __name__ == "__main__":
    main()
