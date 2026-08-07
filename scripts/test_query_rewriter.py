from backend.query_rewriting import QueryRewriter


def main() -> None:
    rewriter = QueryRewriter(
        model_name="qwen3:4b-instruct",
        num_rewrites=2,
    )

    query = "How does LangGraph persist state between executions?"

    queries = rewriter.rewrite(query)

    print("=" * 80)
    print("QUERY REWRITER TEST")
    print("=" * 80)

    for index, rewritten_query in enumerate(queries):
        label = "ORIGINAL" if index == 0 else f"REWRITE {index}"

        print()
        print(f"{label}:")
        print(rewritten_query)

    assert len(queries) == 3
    assert queries[0] == query

    print()
    print("Test passed.")


if __name__ == "__main__":
    main()