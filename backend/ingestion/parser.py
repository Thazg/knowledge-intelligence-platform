import re
from html.parser import HTMLParser

from backend.ingestion.id_generator import generate_document_id
from backend.ingestion.models import Document, DocumentFile

DATA_IMAGE_PATTERN = re.compile(
    r"data:image/[^;,\s\"')]+;base64,[A-Za-z0-9+/=\r\n]+",
)


class _HTMLTextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }

    SKIP_TAGS = {
        "noscript",
        "script",
        "style",
        "template",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0
        self._heading_level: int | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth:
            return

        if tag in self.BLOCK_TAGS:
            self._newline()

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_level = int(tag[1])
            self._chunks.append("#" * self._heading_level + " ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return

        if self._skip_depth:
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_level = None

        if tag in self.BLOCK_TAGS:
            self._newline()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return

        text = re.sub(r"\s+", " ", data).strip()

        if text:
            self._chunks.append(text + " ")

    def text(self) -> str:
        content = "".join(self._chunks)
        content = re.sub(r"[ \t]+\n", "\n", content)
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()

    def _newline(self) -> None:
        if self._chunks and not self._chunks[-1].endswith("\n"):
            self._chunks.append("\n")


class DocumentParser:

    def parse(
        self,
        document_file: DocumentFile,
    ) -> Document:

        raw_content = document_file.path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        content = self._parse_content(
            raw_content,
            document_file.extension,
        )

        return Document(
            document_id=generate_document_id(
                source=document_file.source,
                relative_path=document_file.relative_path,
            ),
            content=content,
            source=document_file.source,
            filename=document_file.filename,
            relative_path=document_file.relative_path,
            extension=document_file.extension,
        )

    def _parse_content(
        self,
        content: str,
        extension: str,
    ) -> str:

        content = self._strip_embedded_data_images(content)

        if extension == ".html":
            return self._parse_html(content)

        if extension == ".rst":
            return self._parse_rst(content)

        return content

    def _strip_embedded_data_images(self, content: str) -> str:
        return DATA_IMAGE_PATTERN.sub(
            "[embedded image omitted]",
            content,
        )

    def _parse_html(self, content: str) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(content)
        parser.close()
        return parser.text()

    def _parse_rst(self, content: str) -> str:
        lines = content.splitlines()
        parsed_lines: list[str] = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

            if self._is_rst_heading(line, next_line):
                level = self._rst_heading_level(next_line[0])
                parsed_lines.append("#" * level + " " + line.strip())
                i += 2
                continue

            parsed_lines.append(line)
            i += 1

        return "\n".join(parsed_lines)

    def _is_rst_heading(
        self,
        line: str,
        underline: str,
    ) -> bool:

        if not line.strip() or not underline:
            return False

        if len(underline) < len(line.strip()):
            return False

        return len(set(underline)) == 1 and underline[0] in "=-~^\"'"

    def _rst_heading_level(self, marker: str) -> int:
        return {
            "=": 1,
            "-": 2,
            "~": 3,
            "^": 4,
            '"': 5,
            "'": 6,
        }.get(marker, 2)
