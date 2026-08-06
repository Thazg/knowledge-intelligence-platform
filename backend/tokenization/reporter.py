from statistics import mean, median

from backend.ingestion.models import Document


class TokenizationReporter:
    def print_summary(
        self,
        documents: list[Document],
    ) -> None:
        print()
        print("=" * 60)
        print("TOKENIZATION REPORT")
        print("=" * 60)

        if not documents:
            print("No documents available.")
            return

        token_counts = [document.token_count for document in documents]

        total_documents = len(documents)
        total_tokens = sum(token_counts)

        average_tokens = mean(token_counts)
        median_tokens = median(token_counts)

        minimum_tokens = min(token_counts)
        maximum_tokens = max(token_counts)

        over_512 = sum(token_count > 512 for token_count in token_counts)

        over_1000 = sum(token_count > 1_000 for token_count in token_counts)

        over_2000 = sum(token_count > 2_000 for token_count in token_counts)

        print(f"Documents          : {total_documents:,}")
        print(f"Total tokens       : {total_tokens:,}")
        print(f"Average tokens/doc : {average_tokens:,.2f}")
        print(f"Median tokens/doc  : {median_tokens:,.2f}")
        print(f"Minimum tokens     : {minimum_tokens:,}")
        print(f"Maximum tokens     : {maximum_tokens:,}")

        print()
        print("DOCUMENT LENGTH DISTRIBUTION")
        print("-" * 60)

        print(
            f"Documents > 512 tokens   : "
            f"{over_512:,} "
            f"({over_512 / total_documents:.2%})"
        )

        print(
            f"Documents > 1,000 tokens : "
            f"{over_1000:,} "
            f"({over_1000 / total_documents:.2%})"
        )

        print(
            f"Documents > 2,000 tokens : "
            f"{over_2000:,} "
            f"({over_2000 / total_documents:.2%})"
        )
