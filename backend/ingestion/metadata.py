import re

from backend.ingestion.models import Document

TITLE_PATTERN = re.compile(
    r"^#\s+(.+)$",
    re.MULTILINE,
)

FRONTMATTER_TITLE_PATTERN = re.compile(
    r"^---\s*\n.*?^title:\s*[\"']?(.+?)[\"']?\s*$.*?^---\s*$",
    re.MULTILINE | re.DOTALL,
)

HEADING_PATTERN = re.compile(
    r"^#{1,6}\s+(.+)$",
    re.MULTILINE,
)


class MetadataExtractor:

    def extract(
        self,
        document: Document,
    ) -> Document:

        title_match = TITLE_PATTERN.search(document.content)

        frontmatter_title_match = FRONTMATTER_TITLE_PATTERN.search(
            document.content
        )

        if frontmatter_title_match:
            document.title = frontmatter_title_match.group(1).strip()
        elif title_match:
            document.title = title_match.group(1).strip()

        document.headings = HEADING_PATTERN.findall(document.content)

        if not document.title and document.headings:
            document.title = document.headings[0].strip()

        document.word_count = len(document.content.split())

        return document
