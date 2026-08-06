from numpy.typing import NDArray
import numpy as np

from sentence_transformers import SentenceTransformer


class LocalEmbedder:

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str | None = None,
    ) -> None:

        self.model_name = model_name

        self.model = SentenceTransformer(
            model_name_or_path=model_name,
            device=device,
        )

    @property
    def dimension(self) -> int:
        dimension = (
            self.model.get_embedding_dimension()
        )

        if dimension is None:
            raise RuntimeError(
                "Unable to determine embedding dimension."
            )

        return dimension

    def embed_documents(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> NDArray[np.float32]:

        if not texts:
            return np.empty(
                shape=(0, self.dimension),
                dtype=np.float32,
            )

        embeddings = self.model.encode(
            sentences=texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embeddings.astype(
            np.float32,
            copy=False,
        )
        
    def embed_query(
        self,
        query: str,
    ) -> NDArray[np.float32]:

        if not query.strip():
            raise ValueError(
                "Query must not be empty."
            )

        instruction = (
            "Represent this sentence for searching "
            "relevant passages: "
        )

        query_text = instruction + query

        embedding = self.model.encode(
            sentences=query_text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embedding.astype(
            np.float32,
            copy=False,
        )