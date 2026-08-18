from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from qdrant_client import models


class RankBM25QueryEncoder:
    def __init__(
        self,
        artifact_path: Path,
    ) -> None:
        artifact = json.loads(
            artifact_path.read_text(
                encoding="utf-8"
            )
        )

        self._validate_artifact(
            artifact
        )

        tokenization = artifact[
            "tokenization"
        ]

        self.pattern = re.compile(
            str(
                tokenization[
                    "pattern"
                ]
            )
        )

        self.lowercase = bool(
            tokenization[
                "lowercase"
            ]
        )

        terms = artifact[
            "sparse"
        ]["terms"]

        self.term_table: dict[
            str,
            tuple[int, float],
        ] = {
            str(term): (
                int(values[0]),
                float(values[1]),
            )
            for term, values
            in terms.items()
        }

        self.vector_name = str(
            artifact[
                "sparse"
            ]["vector_name"]
        )

        self.corpus_sha256 = str(
            artifact[
                "corpus"
            ]["sha256"]
        )

        self.corpus_chunks = int(
            artifact[
                "corpus"
            ]["chunks"]
        )

    @staticmethod
    def _validate_artifact(
        artifact: dict[str, Any],
    ) -> None:
        if artifact.get("version") != 1:
            raise ValueError(
                "Unsupported rank_bm25 "
                "query artifact version."
            )

        if (
            artifact.get("kind")
            != "rank_bm25_query_encoder"
        ):
            raise ValueError(
                "Unexpected query artifact kind."
            )

        try:
            tokenization = artifact[
                "tokenization"
            ]
            sparse = artifact["sparse"]
            corpus = artifact["corpus"]

            pattern = tokenization[
                "pattern"
            ]
            lowercase = tokenization[
                "lowercase"
            ]
            vector_name = sparse[
                "vector_name"
            ]
            terms = sparse["terms"]
            corpus_sha256 = corpus[
                "sha256"
            ]
            corpus_chunks = corpus[
                "chunks"
            ]
        except KeyError as exc:
            raise ValueError(
                "Incomplete rank_bm25 "
                "query artifact."
            ) from exc

        if not isinstance(
            pattern,
            str,
        ) or not pattern:
            raise ValueError(
                "Artifact token pattern "
                "must not be empty."
            )

        if not isinstance(
            lowercase,
            bool,
        ):
            raise ValueError(
                "Artifact lowercase flag "
                "must be boolean."
            )

        if not isinstance(
            vector_name,
            str,
        ) or not vector_name:
            raise ValueError(
                "Artifact vector_name "
                "must not be empty."
            )

        if not isinstance(
            terms,
            dict,
        ):
            raise ValueError(
                "Artifact terms must "
                "be a mapping."
            )

        if not isinstance(
            corpus_sha256,
            str,
        ) or not corpus_sha256:
            raise ValueError(
                "Artifact corpus sha256 "
                "must not be empty."
            )

        if (
            not isinstance(
                corpus_chunks,
                int,
            )
            or corpus_chunks <= 0
        ):
            raise ValueError(
                "Artifact corpus chunk count "
                "must be greater than 0."
            )

        for term, values in terms.items():
            if (
                not isinstance(term, str)
                or not term
            ):
                raise ValueError(
                    "Artifact term keys "
                    "must be non-empty strings."
                )

            if (
                not isinstance(
                    values,
                    list,
                )
                or len(values) != 2
            ):
                raise ValueError(
                    "Artifact term values "
                    "must be [index, idf]."
                )

            index, idf = values

            if (
                not isinstance(index, int)
                or index <= 0
            ):
                raise ValueError(
                    "Artifact sparse index "
                    "must be greater than 0."
                )

            if not isinstance(
                idf,
                (int, float),
            ):
                raise ValueError(
                    "Artifact IDF must "
                    "be numeric."
                )

    def tokenize(
        self,
        text: str,
    ) -> list[str]:
        if self.lowercase:
            text = text.lower()

        return self.pattern.findall(
            text
        )

    def encode(
        self,
        query: str,
    ) -> models.SparseVector | None:
        if not query.strip():
            raise ValueError(
                "query must not be empty."
            )

        tokens = self.tokenize(
            query
        )

        if not tokens:
            return None

        counts = Counter(tokens)

        entries: list[
            tuple[int, float]
        ] = []

        for term, frequency in (
            counts.items()
        ):
            values = self.term_table.get(
                term
            )

            if values is None:
                continue

            index, idf = values

            value = (
                idf
                * frequency
            )

            if value == 0:
                continue

            entries.append(
                (
                    index,
                    float(value),
                )
            )

        if not entries:
            return None

        entries.sort(
            key=lambda item: item[0]
        )

        return models.SparseVector(
            indices=[
                index
                for index, _ in entries
            ],
            values=[
                value
                for _, value in entries
            ],
        )