from __future__ import annotations

import json
from pathlib import Path


class FrozenQueryRewriter:
    def __init__(
        self,
        rewrites_path: Path,
    ) -> None:
        self.rewrites_by_query: dict[str, list[str]] = {}

        with rewrites_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)

                original_query = record[
                    "original_query"
                ]

                rewrites = record[
                    "rewrites"
                ]

                self.rewrites_by_query[
                    original_query
                ] = rewrites

    def rewrite(
        self,
        query: str,
    ) -> list[str]:
        query = query.strip()

        if not query:
            raise ValueError(
                "query must not be empty"
            )

        if query not in self.rewrites_by_query:
            raise KeyError(
                f"No frozen rewrites found for query: "
                f"{query}"
            )

        return [
            query,
            *self.rewrites_by_query[query],
        ]