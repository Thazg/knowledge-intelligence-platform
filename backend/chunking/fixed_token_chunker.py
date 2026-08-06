import hashlib

from backend.chunking.models import Chunk
from backend.ingestion.models import Document
from backend.tokenization.tokenizer import DocumentTokenizer


class FixedTokenChunker:
    def __init__(
        self,
        tokenizer: DocumentTokenizer,
        chunk_size: int = 384,
        chunk_overlap: int = 64,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0.")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.tokenizer = tokenizer
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.step_size = chunk_size - chunk_overlap

    def chunk_document(
        self,
        document: Document,
    ) -> list[Chunk]:
        encoded_with_offsets = self.tokenizer.encode_with_offsets(
            document.content
        )

        if encoded_with_offsets is None:
            token_ids = self.tokenizer.encode(document.content)
            offsets: list[tuple[int, int]] | None = None
        else:
            token_ids, offsets = encoded_with_offsets

        if not token_ids:
            return []

        chunks: list[Chunk] = []

        chunk_index = 0

        for start_index in range(
            0,
            len(token_ids),
            self.step_size,
        ):

            end_index = start_index + self.chunk_size

            chunk_token_ids = token_ids[start_index:end_index]
            chunk_offsets = (
                None
                if offsets is None
                else offsets[start_index:end_index]
            )

            if not chunk_token_ids:
                break

            chunk_token_ids, chunk_offsets = (
                self._trim_leading_continuation_tokens(
                    chunk_token_ids,
                    chunk_offsets,
                )
            )

            chunk_content, actual_token_count = self._build_chunk_content(
                document.content,
                chunk_token_ids,
                chunk_offsets,
            )

            if not chunk_content:
                continue

            chunk_id = self._generate_chunk_id(
                document_id=document.document_id,
                chunk_index=chunk_index,
            )

            chunk = Chunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                content=chunk_content,
                chunk_index=chunk_index,
                token_count=actual_token_count,
                source=document.source,
                filename=document.filename,
                relative_path=document.relative_path.as_posix(),
                title=document.title,
            )

            chunks.append(chunk)

            chunk_index += 1

            if end_index >= len(token_ids):
                break

        return chunks

    def _trim_leading_continuation_tokens(
        self,
        token_ids: list[int],
        offsets: list[tuple[int, int]] | None = None,
    ) -> tuple[list[int], list[tuple[int, int]] | None]:
        trimmed_token_ids = token_ids.copy()
        trimmed_offsets = None if offsets is None else offsets.copy()

        while trimmed_token_ids:
            token = self.tokenizer.convert_id_to_token(
                trimmed_token_ids[0]
            )

            if not token.startswith("##"):
                break

            trimmed_token_ids.pop(0)
            if trimmed_offsets is not None:
                trimmed_offsets.pop(0)

        return trimmed_token_ids, trimmed_offsets

    def _build_chunk_content(
        self,
        document_content: str,
        token_ids: list[int],
        offsets: list[tuple[int, int]] | None,
    ) -> tuple[str, int]:
        if offsets is None:
            return self._build_safe_chunk_content(token_ids)

        valid_offsets = [
            offset
            for offset in offsets
            if offset[1] > offset[0]
        ]

        if not valid_offsets:
            return "", 0

        start_char = valid_offsets[0][0]
        end_char = valid_offsets[-1][1]

        content = document_content[start_char:end_char].strip()

        if not content:
            return "", 0

        actual_token_ids = self.tokenizer.encode(content)

        if len(actual_token_ids) <= self.chunk_size:
            return content, len(actual_token_ids)

        return self._build_safe_chunk_content(token_ids)

    def _build_safe_chunk_content(
        self,
        token_ids: list[int],
    ) -> tuple[str, int]:
        current_token_ids = token_ids

        while current_token_ids:
            content = self.tokenizer.decode(current_token_ids).strip()

            if not content:
                return "", 0

            actual_token_ids = self.tokenizer.encode(content)

            if len(actual_token_ids) <= self.chunk_size:
                return content, len(actual_token_ids)

            overflow = len(actual_token_ids) - self.chunk_size

            current_token_ids = current_token_ids[
                : max(0, len(current_token_ids) - overflow)
            ]

        return "", 0

    @staticmethod
    def _generate_chunk_id(
        document_id: str,
        chunk_index: int,
    ) -> str:
        identity = f"{document_id}:{chunk_index}"

        return hashlib.sha256(identity.encode("utf-8")).hexdigest()
