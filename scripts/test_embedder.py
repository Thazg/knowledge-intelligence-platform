import numpy as np

from backend.embedding.embedder import LocalEmbedder


def main() -> None:

    embedder = LocalEmbedder()

    texts = [
        "Docker containers package applications and dependencies.",
        "Containers provide isolated execution environments.",
        "Kubernetes manages containerized workloads.",
    ]

    embeddings = embedder.embed_documents(
        texts=texts,
        batch_size=2,
        show_progress_bar=False,
    )

    print("=" * 60)
    print("LOCAL EMBEDDER TEST")
    print("=" * 60)
    print(f"Model       : {embedder.model_name}")
    print(f"Dimension   : {embedder.dimension}")
    print(f"Shape       : {embeddings.shape}")
    print(f"Data type   : {embeddings.dtype}")

    print()
    print("VECTOR NORMS")
    print("-" * 60)

    for index, embedding in enumerate(embeddings):
        norm = np.linalg.norm(embedding)

        print(
            f"Embedding {index}: "
            f"{norm:.6f}"
        )

    print()
    print("First 10 values:")
    print(embeddings[0][:10])

    assert embeddings.shape == (
        len(texts),
        embedder.dimension,
    )

    assert embeddings.dtype == np.float32

    assert np.allclose(
        np.linalg.norm(embeddings, axis=1),
        1.0,
        atol=1e-5,
    )

    print()
    print("All embedding checks passed.")

    query_embedding = embedder.embed_query(
        "How do Docker containers isolate applications?"
    )

    print()
    print("QUERY EMBEDDING")
    print("-" * 60)
    print(f"Shape : {query_embedding.shape}")
    print(
        f"Norm  : "
        f"{np.linalg.norm(query_embedding):.6f}"
    )

    assert query_embedding.shape == (
        embedder.dimension,
    )

    assert np.isclose(
        np.linalg.norm(query_embedding),
        1.0,
        atol=1e-5,
    )

if __name__ == "__main__":
    main()