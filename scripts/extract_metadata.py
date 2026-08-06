from pathlib import Path

from backend.ingestion.pipeline import IngestionPipeline
from backend.ingestion.reporter import IngestionReporter


def main() -> None:
    pipeline = IngestionPipeline(
        raw_data_dir=Path("data/raw"),
        processed_path=Path("data/processed/documents.jsonl"),
    )

    pipeline.run()

    reporter = IngestionReporter()
    reporter.print_metadata_summary(
        total_documents=pipeline.total_discovered,
        basic_filtered=pipeline.basic_filtered,
        parsed=pipeline.success,
        failed=pipeline.failed,
        accepted=pipeline.accepted,
        missing_headings=pipeline.missing_headings,
        average_words=pipeline.average_words,
        largest_document=pipeline.largest_document,
        smallest_document=pipeline.smallest_document,
        reject_counter=pipeline.reject_counter,
    )


if __name__ == "__main__":
    main()
