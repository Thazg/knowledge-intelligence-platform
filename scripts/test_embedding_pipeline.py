from pathlib import Path

import numpy as np

from backend.embedding.pipeline import (
    EmbeddingPipeline,
)


def main() -> None:

    pipeline = EmbeddingPipeline(
        input_path=Path(
            "data/processed/chunks_fixed.jsonl"
        ),
        batch_size=32,
    )

    chunks, embeddings = pipeline.run(
        limit=100,
        show_progress_bar=True,
    )

    print()
    print("=" * 60)
    print("EMBEDDING PIPELINE TEST")
    print("=" * 60)
    print(f"Chunks loaded : {len(chunks):,}")
    print(f"Shape         : {embeddings.shape}")
    print(f"Data type     : {embeddings.dtype}")
    print(
        f"Dimension     : "
        f"{pipeline.embedder.dimension}"
    )

    if chunks:
        print()
        print("FIRST EMBEDDED CHUNK")
        print("-" * 60)
        print(
            f"Chunk ID    : "
            f"{chunks[0].chunk_id[:16]}..."
        )
        print(
            f"Filename    : "
            f"{chunks[0].filename}"
        )
        print(
            f"Token count : "
            f"{chunks[0].token_count}"
        )
        print(
            f"Vector norm : "
            f"{np.linalg.norm(embeddings[0]):.6f}"
        )
        print(
            f"Vector[:10] : "
            f"{embeddings[0][:10]}"
        )

    assert len(chunks) == 100

    assert embeddings.shape == (
        100,
        pipeline.embedder.dimension,
    )

    assert embeddings.dtype == np.float32

    assert np.allclose(
        np.linalg.norm(
            embeddings,
            axis=1,
        ),
        1.0,
        atol=1e-5,
    )

    print()
    print("All embedding pipeline checks passed.")


if __name__ == "__main__":
    main()