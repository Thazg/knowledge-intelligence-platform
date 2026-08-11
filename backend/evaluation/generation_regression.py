from __future__ import annotations


def check_generation_regression(
    evaluation: dict,
    manifest: dict,
) -> dict:
    failures: list[dict] = []

    hard_gates = manifest["regression"]["hard_gates"]

    for section_name, expected_values in hard_gates.items():
        actual_section = evaluation[section_name]

        for metric_name, expected_value in expected_values.items():
            actual_value = actual_section[metric_name]

            if actual_value != expected_value:
                failures.append(
                    {
                        "type": "hard_gate",
                        "section": section_name,
                        "metric": metric_name,
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )

    format_policy = manifest[
        "regression"
    ]["tolerance_gates"][
        "citation_format_violations"
    ]

    actual_format_count = evaluation[
        "citations"
    ][
        "total_citation_format_violation_count"
    ]

    actual_format_case_ids = set(
        evaluation[
            "citations"
        ][
            "citation_format_violation_case_ids"
        ]
    )

    maximum_format_count = format_policy[
        "maximum_count"
    ]

    allowed_format_case_ids = set(
        format_policy[
            "allowed_case_ids"
        ]
    )

    if actual_format_count > maximum_format_count:
        failures.append(
            {
                "type": "tolerance_gate",
                "metric": (
                    "citation_format_violation_count"
                ),
                "maximum": maximum_format_count,
                "actual": actual_format_count,
            }
        )

    unexpected_format_case_ids = sorted(
        actual_format_case_ids
        - allowed_format_case_ids
    )

    if unexpected_format_case_ids:
        failures.append(
            {
                "type": "tolerance_gate",
                "metric": (
                    "citation_format_violation_case_ids"
                ),
                "allowed": sorted(
                    allowed_format_case_ids
                ),
                "unexpected": (
                    unexpected_format_case_ids
                ),
            }
        )

    return {
        "passed": not failures,
        "failures": failures,
    }