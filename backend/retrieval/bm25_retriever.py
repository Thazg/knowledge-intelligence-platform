import re
from collections import defaultdict

import numpy as np
from rank_bm25 import BM25Okapi

from backend.chunking.models import Chunk
from backend.retrieval.models import RetrievalResult


class BM25Retriever:
    def __init__(
        self,
        chunks: list[Chunk],
    ) -> None:
        if not chunks:
            raise ValueError("chunks must not be empty.")

        self.chunks = chunks

        tokenized_corpus = [
            self._tokenize(chunk.content)
            for chunk in chunks
        ]

        self.index = BM25Okapi(tokenized_corpus)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"[a-z0-9]+(?:[._/-][a-z0-9]+)*",
            text.lower(),
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = None,
        candidate_multiplier: int = 5,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be empty.")

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        if (
            max_chunks_per_document is not None
            and max_chunks_per_document <= 0
        ):
            raise ValueError(
                "max_chunks_per_document must be greater than 0."
            )

        if candidate_multiplier <= 0:
            raise ValueError(
                "candidate_multiplier must be greater than 0."
            )

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = self.index.get_scores(query_tokens)

        search_limit = top_k

        if max_chunks_per_document is not None:
            search_limit = min(
                len(self.chunks),
                top_k * candidate_multiplier,
            )

        candidate_indices = np.argsort(scores)[::-1][
            :search_limit
        ]

        document_counts: dict[str, int] = defaultdict(int)
        results: list[RetrievalResult] = []

        for chunk_position in candidate_indices:
            score = float(scores[chunk_position])

            if score <= 0:
                continue

            chunk = self.chunks[int(chunk_position)]

            if max_chunks_per_document is not None:
                if (
                    document_counts[chunk.document_id]
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[chunk.document_id] += 1

            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    score=score,
                    rank=len(results) + 1,
                    source=chunk.source,
                    filename=chunk.filename,
                    relative_path=chunk.relative_path,
                    chunk_index=chunk.chunk_index,
                    token_count=chunk.token_count,
                    title=chunk.title,
                )
            )

            if len(results) >= top_k:
                break

        return results