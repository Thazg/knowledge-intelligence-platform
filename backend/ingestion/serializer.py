import json
from pathlib import Path
from typing import TextIO

from backend.ingestion.id_generator import generate_document_id
from backend.ingestion.models import Document


class DocumentSerializer:

    def to_record(self, doc: Document) -> dict:
        return {
            "document_id": doc.document_id,
            "source": doc.source,
            "filename": doc.filename,
            "relative_path": str(doc.relative_path),
            "extension": doc.extension,
            "title": doc.title,
            "headings": doc.headings,
            "word_count": doc.word_count,
            "token_count": doc.token_count,
            "content": doc.content,
        }

    def write_jsonl_record(
        self,
        doc: Document,
        output_file: TextIO,
    ) -> None:

        json.dump(
            self.to_record(doc),
            output_file,
            ensure_ascii=False,
        )

        output_file.write("\n")

    def save_jsonl(
        self,
        documents: list[Document],
        output_path: Path,
    ) -> None:

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            for doc in documents:
                self.write_jsonl_record(doc, f)

    def load_jsonl(
        self,
        input_path: Path,
    ) -> list[Document]:
        documents: list[Document] = []

        with input_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            for line in f:
                record = json.loads(line)
                relative_path = Path(record["relative_path"])
                document_id = (
                    record.get("document_id")
                    or generate_document_id(
                        source=record["source"],
                        relative_path=relative_path,
                    )
                )
                document = Document(
                    document_id=document_id,
                    content=record["content"],
                    source=record["source"],
                    filename=record["filename"],
                    relative_path=relative_path,
                    extension=record["extension"],
                    title=record.get("title") or "",
                    headings=record.get("headings", []),
                    word_count=record.get("word_count", 0),
                    token_count=record.get("token_count", 0),
                )
                documents.append(document)

        return documents
