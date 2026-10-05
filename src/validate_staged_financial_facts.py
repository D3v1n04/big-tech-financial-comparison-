"""Validate the standardized financial fact dataset before database loading."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from metric_contract import (
    COMPANIES,
    EXPECTED_STAGED_RECORD_COUNT,
    METRIC_TAG_PRIORITY,
    REQUIRED_METRICS,
    TARGET_FISCAL_YEARS,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = (
    PROJECT_ROOT / "data" / "staged" / "financial_facts_2020_2025.csv"
)
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT / "docs" / "staged_data_validation_report.json"
)

REQUIRED_COLUMNS = {
    "ticker",
    "company_name",
    "cik",
    "metric_name",
    "fiscal_year",
    "value_usd",
    "unit",
    "period_end",
    "source_form",
    "source_filed",
    "source_accession_number",
    "source_taxonomy",
    "source_xbrl_tag",
    "source_url",
    "source_file_sha256",
}

POINT_IN_TIME_METRICS = {
    "total_assets",
    "stockholders_equity",
}

FLOW_METRICS = set(REQUIRED_METRICS) - POINT_IN_TIME_METRICS


def parse_arguments() -> argparse.Namespace:
    """Read optional input and output file paths."""
    parser = argparse.ArgumentParser(
        description="Validate staged Big Tech financial fact data."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Path to the staged financial facts CSV file.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Path for the JSON validation report.",
    )
    return parser.parse_args()


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    details: str,
) -> None:
    """Add one validation result to the report."""
    checks.append(
        {
            "check_name": name,
            "passed": passed,
            "details": details,
        }
    )


def is_valid_sha256(value: str) -> bool:
    """Return whether a string is a SHA 256 hexadecimal digest."""
    return len(value) == 64 and all(
        character in "0123456789abcdef"
        for character in value.lower()
    )


def main() -> None:
    """Run structural, provenance, and financial fact validation checks."""
    arguments = parse_arguments()
    input_path = arguments.input_path.resolve()
    report_path = arguments.report_path.resolve()

    if not input_path.is_file():
        raise SystemExit(f"Staged input file does not exist: {input_path}")

    with input_path.open(encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        rows = list(reader)
        column_names = set(reader.fieldnames or [])

    checks: list[dict[str, Any]] = []

    missing_columns = sorted(REQUIRED_COLUMNS - column_names)
    add_check(
        checks,
        name="required_columns_present",
        passed=not missing_columns,
        details=(
            "All required columns are present."
            if not missing_columns
            else f"Missing columns: {missing_columns}"
        ),
    )

    add_check(
        checks,
        name="expected_record_count",
        passed=len(rows) == EXPECTED_STAGED_RECORD_COUNT,
        details=(
            f"Found {len(rows)} records; "
            f"expected {EXPECTED_STAGED_RECORD_COUNT}."
        ),
    )

    record_keys = [
        (row["ticker"], row["metric_name"], row["fiscal_year"])
        for row in rows
    ]
    duplicate_keys = [
        key
        for key, count in Counter(record_keys).items()
        if count > 1
    ]
    add_check(
        checks,
        name="unique_company_metric_year_key",
        passed=not duplicate_keys,
        details=(
            "All company, metric, and fiscal year combinations are unique."
            if not duplicate_keys
            else f"Duplicate keys: {sorted(duplicate_keys)}"
        ),
    )

    expected_keys = {
        (ticker, metric_name, str(fiscal_year))
        for ticker in COMPANIES
        for metric_name in REQUIRED_METRICS
        for fiscal_year in TARGET_FISCAL_YEARS
    }
    actual_keys = set(record_keys)
    missing_keys = sorted(expected_keys - actual_keys)
    unexpected_keys = sorted(actual_keys - expected_keys)
    add_check(
        checks,
        name="complete_expected_company_metric_year_coverage",
        passed=not missing_keys and not unexpected_keys,
        details=(
            "All expected company, metric, and fiscal year combinations exist."
            if not missing_keys and not unexpected_keys
            else f"Missing: {missing_keys}; unexpected: {unexpected_keys}"
        ),
    )

    blank_required_values = []

    for row_number, row in enumerate(rows, start=2):
        for column_name in REQUIRED_COLUMNS:
            if not row.get(column_name, "").strip():
                blank_required_values.append(
                    f"row {row_number}: {column_name}"
                )

    add_check(
        checks,
        name="required_values_not_blank",
        passed=not blank_required_values,
        details=(
            "All required values are populated."
            if not blank_required_values
            else f"Blank values: {blank_required_values}"
        ),
    )

    invalid_rows = []

    for row_number, row in enumerate(rows, start=2):
        ticker = row["ticker"]
        metric_name = row["metric_name"]

        try:
            fiscal_year = int(row["fiscal_year"])
            value_usd = float(row["value_usd"])
            period_end = date.fromisoformat(row["period_end"])
            filed_date = date.fromisoformat(row["source_filed"])
        except ValueError as error:
            invalid_rows.append(
                f"row {row_number}: invalid type or date ({error})"
            )
            continue

        if ticker not in COMPANIES:
            invalid_rows.append(f"row {row_number}: unknown ticker {ticker}")

        if metric_name not in REQUIRED_METRICS:
            invalid_rows.append(
                f"row {row_number}: unknown metric {metric_name}"
            )

        if row["unit"] != "USD":
            invalid_rows.append(
                f"row {row_number}: expected USD, found {row['unit']}"
            )

        if fiscal_year != period_end.year:
            invalid_rows.append(
                f"row {row_number}: fiscal year {fiscal_year} does not "
                f"match period end {row['period_end']}"
            )

        if not row["source_form"].startswith("10-K"):
            invalid_rows.append(
                f"row {row_number}: source form is {row['source_form']}"
            )

        if row["source_taxonomy"] != "us-gaap":
            invalid_rows.append(
                f"row {row_number}: taxonomy is {row['source_taxonomy']}"
            )

        allowed_tags = METRIC_TAG_PRIORITY.get(ticker, {}).get(
            metric_name,
            (),
        )

        if row["source_xbrl_tag"] not in allowed_tags:
            invalid_rows.append(
                f"row {row_number}: unexpected tag "
                f"{row['source_xbrl_tag']}"
            )

        if not row["source_url"].startswith(
            "https://data.sec.gov/api/xbrl/companyfacts/"
        ):
            invalid_rows.append(
                f"row {row_number}: invalid source URL"
            )

        if not is_valid_sha256(row["source_file_sha256"]):
            invalid_rows.append(
                f"row {row_number}: invalid source SHA 256"
            )

        if metric_name in FLOW_METRICS:
            try:
                period_start = date.fromisoformat(row["period_start"])
            except ValueError:
                invalid_rows.append(
                    f"row {row_number}: missing or invalid flow start date"
                )
                continue

            duration_days = (period_end - period_start).days

            if not 300 <= duration_days <= 380:
                invalid_rows.append(
                    f"row {row_number}: unexpected flow duration "
                    f"{duration_days} days"
                )

        if metric_name in POINT_IN_TIME_METRICS and row["period_start"]:
            invalid_rows.append(
                f"row {row_number}: point in time metric has "
                f"period start {row['period_start']}"
            )

        if metric_name in {
            "revenue",
            "total_assets",
            "capital_expenditures",
        } and value_usd <= 0:
            invalid_rows.append(
                f"row {row_number}: expected positive value, "
                f"found {value_usd}"
            )

        if filed_date.year < fiscal_year:
            invalid_rows.append(
                f"row {row_number}: filing date precedes fiscal year"
            )

    add_check(
        checks,
        name="business_rules_and_source_provenance",
        passed=not invalid_rows,
        details=(
            "All values, dates, source fields, tags, units, and "
            "business rules passed."
            if not invalid_rows
            else f"Validation issues: {invalid_rows}"
        ),
    )

    report = {
        "input_file": str(input_path),
        "record_count": len(rows),
        "checks": checks,
        "overall_status": (
            "passed"
            if all(check["passed"] for check in checks)
            else "failed"
        ),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    passed_checks = sum(check["passed"] for check in checks)

    print(
        f"Validation completed: {passed_checks}/{len(checks)} checks passed."
    )
    print(f"Validation report: {report_path}")

    if report["overall_status"] != "passed":
        raise SystemExit("Staged financial data validation failed.")


if __name__ == "__main__":
    main()
