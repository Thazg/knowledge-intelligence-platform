from backend.ingestion.models import Document

MIN_WORDS = 20

MAX_HEADINGS = 500

MAX_LONG_TOKEN_CHARS = 100_000


class QualityFilter:

    def validate(
        self,
        document: Document,
    ) -> tuple[bool, str | None]:

        if not document.content.strip():
            return False, "empty_content"

        if "data:image/" in document.content:
            return False, "embedded_data_uri"

        longest_run = self._longest_nonspace_run(document.content)

        if longest_run > MAX_LONG_TOKEN_CHARS:
            return False, "long_unbroken_text"

        if document.word_count < MIN_WORDS:
            return False, "too_short"

        if len(document.headings) > MAX_HEADINGS:
            return False, "too_many_headings"

        return True, None

    def _longest_nonspace_run(
        self,
        content: str,
    ) -> int:

        longest = 0
        current = 0

        for char in content:
            if char.isspace():
                longest = max(longest, current)
                current = 0
            else:
                current += 1

        return max(longest, current)
