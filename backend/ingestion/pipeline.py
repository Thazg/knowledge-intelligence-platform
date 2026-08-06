import traceback
from collections import Counter
from pathlib import Path

from backend.ingestion.basic_filter import DocumentFilter
from backend.ingestion.discovery import DocumentDiscovery
from backend.ingestion.metadata import MetadataExtractor
from backend.ingestion.models import Document
from backend.ingestion.normalizer import DocumentNormalizer
from backend.ingestion.parser import DocumentParser
from backend.ingestion.quality_filter import QualityFilter
from backend.ingestion.serializer import DocumentSerializer


class IngestionPipeline:
    def __init__(
        self,
        raw_data_dir: Path,
        processed_path: Path,
        collect_documents: bool = False,
    ) -> None:
        self.discovery = DocumentDiscovery(raw_data_dir)
        self.filter = DocumentFilter()
        self.parser = DocumentParser()
        self.normalizer = DocumentNormalizer()
        self.extractor = MetadataExtractor()
        self.quality_filter = QualityFilter()
        self.serializer = DocumentSerializer()

        self.processed_path = processed_path
        self.collect_documents = collect_documents

        self.total_discovered = 0
        self.basic_filtered = 0
        self.success = 0
        self.failed = 0
        self.accepted = 0
        self.rejected = 0
        self.missing_headings = 0
        self.word_counts: list[int] = []
        self.accepted_documents: list[Document] = []
        self.largest_document: Document | None = None
        self.smallest_document: Document | None = None

        self.reject_counter = Counter(
            {
                "empty_content": 0,
                "embedded_data_uri": 0,
                "long_unbroken_text": 0,
                "too_short": 0,
                "too_many_headings": 0,
            }
        )

    def run(self) -> list[Document]:
        documents = self.discovery.discover()
        self.total_discovered = len(documents)

        self.processed_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        temp_processed_path = self.processed_path.with_name(
            f"{self.processed_path.name}.tmp"
        )

        with temp_processed_path.open(
            "w",
            encoding="utf-8",
        ) as output_file:
            for document_file in documents:
                try:
                    # Basic Filter
                    if not self.filter.is_valid(document_file):
                        self.basic_filtered += 1
                        continue

                    # Parse
                    document = self.parser.parse(document_file)

                    if document is None:
                        self.failed += 1
                        continue

                    # Normalize
                    document = self.normalizer.normalize(document)

                    # Metadata
                    document = self.extractor.extract(document)

                    self.success += 1

                    # Quality Filter
                    is_valid, reason = self.quality_filter.validate(document)

                    if not is_valid:
                        self.rejected += 1
                        self.reject_counter[reason or "unknown"] += 1
                        continue

                    self.accepted += 1

                    if self.collect_documents:
                        self.accepted_documents.append(document)

                    self.serializer.write_jsonl_record(
                        document,
                        output_file,
                    )

                    if not document.headings:
                        self.missing_headings += 1

                    self.word_counts.append(document.word_count)

                    if (
                        self.largest_document is None
                        or document.word_count > self.largest_document.word_count
                    ):
                        self.largest_document = document

                    if (
                        self.smallest_document is None
                        or document.word_count < self.smallest_document.word_count
                    ):
                        self.smallest_document = document

                except Exception:
                    self.failed += 1
                    traceback.print_exc()

        temp_processed_path.replace(self.processed_path)
        return self.accepted_documents

    @property
    def average_words(self) -> float:
        if not self.word_counts:
            return 0.0
        return sum(self.word_counts) / len(self.word_counts)
