from transformers import AutoTokenizer


class DocumentTokenizer:
    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self.model_name = model_name

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def encode(
        self,
        text: str,
    ) -> list[int]:
        if not text:
            return []

        return self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )

    def encode_with_offsets(
        self,
        text: str,
    ) -> tuple[list[int], list[tuple[int, int]]] | None:
        if not text:
            return [], []

        try:
            encoded = self.tokenizer(
                text,
                add_special_tokens=False,
                return_offsets_mapping=True,
            )
        except NotImplementedError:
            return None

        token_ids = list(encoded["input_ids"])
        offsets = [
            (int(start), int(end))
            for start, end in encoded["offset_mapping"]
        ]

        return token_ids, offsets

    def decode(
        self,
        token_ids: list[int],
    ) -> str:
        if not token_ids:
            return ""

        return self.tokenizer.decode(
            token_ids,
            skip_special_tokens=True,
        )

    def convert_id_to_token(
        self,
        token_id: int,
    ) -> str:
        return self.tokenizer.convert_ids_to_tokens(token_id)

    def count_tokens(
        self,
        text: str,
    ) -> int:
        return len(self.encode(text))
