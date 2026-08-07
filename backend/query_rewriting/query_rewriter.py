from __future__ import annotations

import ollama


class QueryRewriter:
    def __init__(
        self,
        model_name: str = "qwen3:4b-instruct",
        num_rewrites: int = 2,
    ) -> None:
        if num_rewrites < 1:
            raise ValueError("num_rewrites must be >= 1")

        self.model_name = model_name
        self.num_rewrites = num_rewrites

    def rewrite(self, query: str) -> list[str]:
        query = query.strip()

        if not query:
            raise ValueError("query must not be empty")

        prompt = self._build_prompt(query)

        response = ollama.generate(
            model=self.model_name,
            prompt=prompt,
            options={
                "temperature": 0.0,
                "seed": 42,
            },
        )

        raw_output = response["response"].strip()

        rewrites = self._parse_rewrites(raw_output)

        return [query, *rewrites]

    def _build_prompt(self, query: str) -> str:
        return f"""
Rewrite the following technical search query into exactly
{self.num_rewrites} alternative queries for document retrieval.

Requirements:
- Preserve the original intent.
- Do not answer the question.
- Do not add new facts.
- Use concise technical terminology.
- Each rewrite should express the same information need differently.
- Return exactly {self.num_rewrites} lines.
- Do not number the lines.
- Do not include bullets.
- Do not include explanations.

Query:
{query}
""".strip()

    def _parse_rewrites(self, output: str) -> list[str]:
        lines = [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

        if len(lines) < self.num_rewrites:
            raise ValueError(
                f"Expected {self.num_rewrites} rewrites, "
                f"but received {len(lines)}."
            )

        rewrites = lines[: self.num_rewrites]

        return rewrites