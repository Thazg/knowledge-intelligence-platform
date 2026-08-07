from backend.reranking.cross_encoder_reranker import (
    CrossEncoderReranker,
)
from backend.retrieval.models import RetrievalResult


def create_candidate(
    chunk_id: str,
    content: str,
    rank: int,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=f"document-{chunk_id}",
        content=content,
        score=0.0,
        rank=rank,
        source="test",
        filename=f"{chunk_id}.md",
        relative_path=f"test/{chunk_id}.md",
        chunk_index=0,
        token_count=len(content.split()),
        title=None,
    )


def main() -> None:
    query = (
        "What is Docker BuildKit and how does it "
        "differ from the legacy builder?"
    )

    candidates = [
        create_candidate(
            chunk_id="irrelevant-kubernetes",
            content=(
                "A Kubernetes Service exposes a group "
                "of Pods over a stable network endpoint."
            ),
            rank=1,
        ),
        create_candidate(
            chunk_id="buildkit-overview",
            content=(
                "BuildKit is Docker's modern builder "
                "backend. It improves build performance, "
                "supports parallel execution, and replaces "
                "the older legacy builder."
            ),
            rank=2,
        ),
        create_candidate(
            chunk_id="fastapi-background-task",
            content=(
                "FastAPI background tasks run after "
                "returning an HTTP response."
            ),
            rank=3,
        ),
    ]

    reranker = CrossEncoderReranker(
        model_name=(
            "cross-encoder/ms-marco-MiniLM-L6-v2"
        ),
        batch_size=8,
    )

    results = reranker.rerank(
        query=query,
        candidates=candidates,
        top_k=3,
    )

    print("=" * 80)
    print("CROSS-ENCODER RERANKER TEST")
    print("=" * 80)

    for result in results:
        print()
        print(f"Rank    : {result.rank}")
        print(f"Score   : {result.score:.6f}")
        print(f"Chunk ID: {result.chunk_id}")
        print(f"Content : {result.content}")

    assert len(results) == 3
    assert results[0].chunk_id == "buildkit-overview"

    assert all(
        result.rank == expected_rank
        for expected_rank, result in enumerate(
            results,
            start=1,
        )
    )

    print()
    print("All cross-encoder reranker checks passed.")


if __name__ == "__main__":
    main()