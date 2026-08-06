from pathlib import Path

from backend.tokenization.pipeline import TokenizationPipeline
from backend.tokenization.reporter import TokenizationReporter


def main() -> None:
    pipeline = TokenizationPipeline(
        input_path=Path("data/processed/documents.jsonl"),
        output_path=Path("data/processed/documents_tokenized.jsonl"),
    )

    documents = pipeline.run()

    reporter = TokenizationReporter()

    reporter.print_summary(documents)

    print("=" * 60)
    print("TOKENIZATION COMPLETED")
    print("=" * 60)
    print(f"Documents: {len(documents):,}")
    print(
        "Total tokens:",
        f"{sum(doc.token_count for doc in documents):,}",
    )
    print()
    print("FIRST DOCUMENT")
    print("-" * 60)
    if not documents:
        print("None")
        return

    print(f"Filename: {documents[0].filename}")
    print(f"Words: {documents[0].word_count:,}")
    print(f"Tokens: {documents[0].token_count:,}")


if __name__ == "__main__":
    main()
