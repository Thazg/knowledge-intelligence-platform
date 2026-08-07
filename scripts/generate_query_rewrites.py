import json
from pathlib import Path

from backend.query_rewriting.query_rewriter import QueryRewriter

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "datasets"
    / "retrieval_cases.jsonl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "datasets"
    / "query_rewrites.jsonl"
)


def load_active_cases(path: Path) -> list[dict]:
    cases: list[dict] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            if record.get("status") != "active":
                continue

            cases.append(record)

    return cases


def main() -> None:
    cases = load_active_cases(DATASET_PATH)

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    rewriter = QueryRewriter(
        model_name="qwen3:4b-instruct",
        num_rewrites=2,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 80)
    print("GENERATING FROZEN QUERY REWRITES")
    print("=" * 80)
    print(f"Cases : {len(cases)}")
    print(f"Output: {OUTPUT_PATH}")

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for index, case in enumerate(
            cases,
            start=1,
        ):
            case_id = case["id"]
            original_query = case["query"]

            queries = rewriter.rewrite(
                original_query
            )

            rewrites = queries[1:]

            record = {
                "case_id": case_id,
                "original_query": original_query,
                "rewrites": rewrites,
            }

            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

            print()
            print(
                f"[{index}/{len(cases)}] "
                f"{case_id}"
            )
            print(
                f"Original : {original_query}"
            )

            for rewrite_index, rewrite in enumerate(
                rewrites,
                start=1,
            ):
                print(
                    f"Rewrite {rewrite_index}: "
                    f"{rewrite}"
                )

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print(
        f"Saved frozen rewrites to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()