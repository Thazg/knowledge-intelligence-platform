from pathlib import Path

from backend.ingestion.models import Document
from backend.ingestion.serializer import DocumentSerializer
from backend.tokenization.tokenizer import DocumentTokenizer


class TokenizationPipeline:
    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self.input_path = input_path
        self.output_path = output_path

        self.serializer = DocumentSerializer()

        self.tokenizer = DocumentTokenizer(
            model_name=model_name,
        )

    def run(self) -> list[Document]:
        documents = self.serializer.load_jsonl(self.input_path)

        for document in documents:
            document.token_count = self.tokenizer.count_tokens(
                document.content
            )

        self.serializer.save_jsonl(
            documents=documents,
            output_path=self.output_path,
        )

        return documents
