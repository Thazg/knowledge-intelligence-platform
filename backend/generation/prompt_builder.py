from __future__ import annotations

from dataclasses import dataclass

from backend.generation.models import GenerationContext


@dataclass(frozen=True)
class PromptMessages:
    system_prompt: str
    user_prompt: str


class PromptBuilder:
    SYSTEM_PROMPT = """You are an enterprise technical documentation assistant.

Answer the user's question using only the provided sources.

Rules:
1. Do not use knowledge that is not supported by the provided sources.
2. Cite factual claims using citations exactly in the form [1], [2], or [1][3].
3. Never write citations as [SOURCE 1], [SOURCE 2], or any other format.
4. Only cite source IDs that appear in the provided context.
5. If the provided sources are insufficient to answer the question reliably, say that the available evidence is insufficient.
6. When multiple sources disagree, explicitly describe the disagreement and cite the relevant sources.
7. Prefer precise technical answers over speculation.
8. Do not include a separate references section unless the user explicitly asks for one.
9. Prefer concise answers and avoid repeating the same conclusion or recommendation.
10. Answer the question directly before adding supporting detail.
11. Only treat a question as ambiguous when missing information prevents a reliable direct answer. Do not call a question ambiguous merely because additional context could be useful.
12. If a question is genuinely ambiguous, briefly state the most important missing information, then provide at most 3 high-level options supported by the sources.
13. Do not try to use every provided source. Use only the sources directly necessary to answer the question.
14. Finish the answer before reaching the output limit. Prioritize a complete concise answer over additional detail.  
"""

    def build(
        self,
        context: GenerationContext,
    ) -> PromptMessages:
        if not context.query.strip():
            raise ValueError("context.query must not be empty")

        if not context.context_text.strip():
            return PromptMessages(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=self._build_no_context_prompt(context.query),
            )

        return PromptMessages(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=self._build_user_prompt(context),
        )

    @staticmethod
    def _build_user_prompt(
        context: GenerationContext,
    ) -> str:
        return f"""Question:
{context.query}

Sources:
{context.context_text}

Answer the question using only the sources above.

Use citations in the form [1], [2], or [1][2] immediately after the claims they support.
"""

    @staticmethod
    def _build_no_context_prompt(query: str) -> str:
        return f"""Question:
{query}

No supporting sources were retrieved.

Respond that the available evidence is insufficient to answer the question reliably.
"""