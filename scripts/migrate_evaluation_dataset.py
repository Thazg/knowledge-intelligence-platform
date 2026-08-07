import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "datasets"
    / "retrieval_cases.jsonl"
)

BACKUP_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "datasets"
    / "retrieval_cases_legacy_backup.jsonl"
)


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    records: list[dict] = []

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}"
                ) from exc

            records.append(record)

    if not records:
        raise ValueError(
            "Evaluation dataset is empty."
        )

    # Create a backup before modifying anything.
    with BACKUP_PATH.open(
        "w",
        encoding="utf-8",
    ) as backup_file:
        for record in records:
            backup_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    migrated_records: list[dict] = []

    migrated_count = 0
    already_new_schema_count = 0

    for record in records:
        case_id = record.get(
            "id",
            "<unknown>",
        )

        # Already migrated.
        if "relevant_documents" in record:
            migrated_records.append(
                record
            )

            already_new_schema_count += 1

            print(
                f"[SKIP] {case_id}: "
                "already uses new schema"
            )

            continue

        expected_source = record.get(
            "expected_source"
        )

        expected_path = record.get(
            "expected_path"
        )

        if (
            expected_source is None
            or expected_path is None
        ):
            raise ValueError(
                f"Case '{case_id}' contains neither "
                "new schema nor complete legacy "
                "expected_source/expected_path fields."
            )

        migrated_record = {
            key: value
            for key, value in record.items()
            if key
            not in {
                "expected_source",
                "expected_path",
            }
        }

        migrated_record[
            "relevant_documents"
        ] = [
            {
                "source": expected_source,
                "path": expected_path,
                "relevance": 3,
            }
        ]

        migrated_records.append(
            migrated_record
        )

        migrated_count += 1

        print(
            f"[MIGRATE] {case_id}"
        )

    with DATASET_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for record in migrated_records:
            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print("=" * 80)
    print("EVALUATION DATASET MIGRATION")
    print("=" * 80)
    print(
        f"Total cases        : "
        f"{len(records)}"
    )
    print(
        f"Migrated           : "
        f"{migrated_count}"
    )
    print(
        f"Already new schema : "
        f"{already_new_schema_count}"
    )
    print(
        f"Backup             : "
        f"{BACKUP_PATH}"
    )
    print(
        f"Dataset            : "
        f"{DATASET_PATH}"
    )


if __name__ == "__main__":
    main()