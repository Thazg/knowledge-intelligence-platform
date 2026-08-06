import re
import unicodedata

from backend.ingestion.models import Document


class DocumentNormalizer:

    def normalize(
        self,
        document: Document,
    ) -> Document:

        content = document.content

        # Normalize line endings
        content = content.replace("\r\n", "\n")
        content = content.replace("\r", "\n")

        # Remove NULL characters
        content = content.replace("\x00", "")

        # Remove UTF-8 byte order mark if present
        content = content.replace("\ufeff", "")

        # Replace tabs with spaces
        content = content.replace("\t", "    ")

        # Remove trailing whitespace
        content = "\n".join(line.rstrip() for line in content.split("\n"))

        # Collapse multiple blank lines
        content = re.sub(
            r"\n{3,}",
            "\n\n",
            content,
        )

        # Unicode normalization
        content = unicodedata.normalize(
            "NFKC",
            content,
        )

        document.content = content

        return document
