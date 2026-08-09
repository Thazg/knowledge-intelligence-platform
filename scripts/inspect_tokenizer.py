from backend.tokenization.tokenizer import DocumentTokenizer


def main() -> None:
    tokenizer = DocumentTokenizer()

    text = (
        "Retrieval-augmented generation combines "
        "information retrieval with language generation."
    )

    token_count = tokenizer.count_tokens(text)

    print(f"Text: {text}")
    print(f"Token count: {token_count:,}")


if __name__ == "__main__":
    main()
