from collections import Counter

from backend.ingestion.models import Document


class IngestionReporter:

    WIDTH = 80

    def divider(self) -> None:
        print("=" * self.WIDTH)

    def section(self, title: str) -> None:
        print()
        print(title)
        print("-" * len(title))

    def print_metadata_summary(
        self,
        total_documents: int,
        basic_filtered: int,
        parsed: int,
        failed: int,
        accepted: int,
        missing_headings: int,
        average_words: float,
        largest_document: Document | None,
        smallest_document: Document | None,
        reject_counter: Counter,
    ) -> None:

        self.divider()
        print("INGESTION SUMMARY")
        self.divider()

        self.section("Discovery")

        print(f"Documents          : {total_documents:,}")
        print(f"Basic Filtered     : {basic_filtered:,}")

        self.section("Parsing")

        print(f"Parsed             : {parsed:,}")
        print(f"Failed             : {failed:,}")

        self.section("Metadata")

        print(f"Missing Headings   : {missing_headings:,}")
        print(f"Average Words      : {average_words:,.0f}")

        self.section("Quality Filter")

        print(f"Accepted           : {accepted:,}")
        print(f"Rejected           : {sum(reject_counter.values()):,}")

        self.section("Rejection Reasons")

        if reject_counter:
            for reason, count in reject_counter.items():
                print(f"{reason:<20}: {count:,}")
        else:
            print("None")

        self.section("Largest Document")

        if largest_document is None:
            print("None")
        else:
            print(f"Source             : {largest_document.source}")
            print(f"Path               : {largest_document.relative_path}")
            print(f"Words              : {largest_document.word_count:,}")

        self.section("Smallest Document")

        if smallest_document is None:
            print("None")
        else:
            print(f"Source             : {smallest_document.source}")
            print(f"Path               : {smallest_document.relative_path}")
            print(f"Words              : {smallest_document.word_count:,}")
