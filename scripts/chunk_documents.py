from pathlib import Path

from backend.chunking.pipeline import ChunkingPipeline
from backend.chunking.reporter import ChunkingReporter
from backend.tokenization import reporter

def main() -> None:

    pipeline = ChunkingPipeline(
        input_path=Path(
            "data/processed/documents_tokenized.jsonl"
        ),
        output_path=Path(
            "data/processed/chunks_fixed.jsonl"
        ),
        chunk_size=384,
        chunk_overlap=64,
    )

    chunks = pipeline.run()
    reporter = ChunkingReporter()

    reporter.print_summary(
        chunks=chunks,
        chunk_size=384,
    )

if __name__ == "__main__":
    main()