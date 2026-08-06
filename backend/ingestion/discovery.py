from pathlib import Path
from typing import Iterable

from backend.ingestion.models import DocumentFile


class DocumentDiscovery:

    SUPPORTED_EXTENSIONS = {
        ".md",
        ".mdx",
        ".rst",
        ".txt",
        ".html",
    }

    IGNORED_DIRECTORIES = {
        ".git",
        "__pycache__",
        "node_modules",
        ".next",
        ".venv",
        "venv",
        "_vendor",
    }

    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory

    def discover(self) -> list[DocumentFile]:

        documents: list[DocumentFile] = []

        if not self.root_directory.exists():
            return documents

        for source_dir in sorted(self.root_directory.iterdir()):

            if not source_dir.is_dir():
                continue

            documents.extend(self._discover_source(source_dir))

        return documents

    def _discover_source(
        self,
        source_directory: Path,
    ) -> Iterable[DocumentFile]:

        source_name = source_directory.name

        for path in sorted(source_directory.rglob("*")):

            if not path.is_file():
                continue

            if any(part in self.IGNORED_DIRECTORIES for part in path.parts):
                continue

            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            yield DocumentFile(
                source=source_name,
                path=path,
                relative_path=path.relative_to(source_directory),
                filename=path.name,
                extension=path.suffix.lower(),
                size_bytes=path.stat().st_size,
            )
