"""Transform raw SEC Company Facts data into a standardized dataset."""

from __future__ import annotations

import argparse
import csv
import json
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
STAGED_DATA_DIRECTORY = PROJECT_ROOT / "data" / "staged"


def parse_arguments() -> argparse.Namespace:
    """Read the raw SEC extraction directory."""
    parser = argparse.ArgumentParser(
        description="Create standardized financial facts from SEC Company Facts."
    )
    parser.add_argument(
        "--run-directory",
        required=True,
        type=Path,
        help="Directory containing downloaded SEC Company Facts JSON files.",
    )
    return parser.parse_args()


def analysis_fiscal_year(fact: dict[str, Any]) -> int | None:
    """Return the year represented by a fact's reporting end date."""
    period_end = fact.get("end", "")

    if not isinstance(period_end, str) or len(period_end) < 4:
        return None

    try:
        return int(period_end[:4])
    except ValueError:
        return None


def is_eligible_annual_fact(fact: dict[str, Any]) -> bool:
    """Return whether a fact is an annual 10 K value in the target period."""
    fiscal_year = analysis_fiscal_year(fact)

    return (
        fact.get("form", "").startswith("10-K")
        and fact.get("fp") == "FY"
        and fiscal_year in TARGET_FISCAL_YEARS
    )


def fact_sort_key(fact: dict[str, Any]) -> tuple[str, str]:
    """Prefer the latest filed fact when restatements or duplicates exist."""
    return (
        str(fact.get("filed", "")),
        str(fact.get("accn", "")),
    )


def load_source_metadata(run_directory: Path) -> dict[str, dict[str, Any]]:
    """Load source URLs and file hashes from the extraction manifest."""
    manifest_path = run_directory / "extraction_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    return {
        file_record["ticker"]: file_record
        for file_record in manifest["files"]
    }


def collect_candidates(
    payload: dict[str, Any],
    ticker: str,
    source_file: Path,
    source_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    """Collect all eligible facts allowed by the metric contract."""
    us_gaap_concepts = payload["facts"].get("us-gaap", {})
    company_name = COMPANIES[ticker]["company_name"]
    candidates: list[dict[str, Any]] = []

    for metric_name in REQUIRED_METRICS:
        tag_priority_list = METRIC_TAG_PRIORITY[ticker][metric_name]

        for tag_priority, xbrl_tag in enumerate(tag_priority_list):
            concept = us_gaap_concepts.get(xbrl_tag)

            if concept is None:
                continue

            for unit, facts in concept["units"].items():
                if unit != "USD":
                    continue

                for fact in facts:
                    if not is_eligible_annual_fact(fact):
                        continue

                    fiscal_year = analysis_fiscal_year(fact)

                    if fiscal_year is None:
                        continue

                    candidates.append(
                        {
                            "ticker": ticker,
                            "company_name": company_name,
                            "cik": COMPANIES[ticker]["cik"],
                            "metric_name": metric_name,
                            "fiscal_year": fiscal_year,
                            "value_usd": fact["val"],
                            "unit": unit,
                            "period_start": fact.get("start", ""),
                            "period_end": fact.get("end", ""),
                            "source_form": fact.get("form", ""),
                            "source_filed": fact.get("filed", ""),
                            "source_accession_number": fact.get("accn", ""),
                            "source_taxonomy": "us-gaap",
                            "source_xbrl_tag": xbrl_tag,
                            "tag_priority": tag_priority,
                            "source_file": source_file.name,
                            "source_url": source_metadata["source_url"],
                            "source_file_sha256": source_metadata["sha256"],
                        }
                    )

    return candidates


def select_contract_facts(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Select one fact per company, metric, and fiscal year."""
    selected_rows = []

    for ticker in COMPANIES:
        for metric_name in REQUIRED_METRICS:
            for fiscal_year in TARGET_FISCAL_YEARS:
                matching_candidates = [
                    candidate
                    for candidate in candidates
                    if candidate["ticker"] == ticker
                    and candidate["metric_name"] == metric_name
                    and candidate["fiscal_year"] == fiscal_year
                ]

                if not matching_candidates:
                    continue

                preferred_priority = min(
                    candidate["tag_priority"]
                    for candidate in matching_candidates
                )

                preferred_candidates = [
                    candidate
                    for candidate in matching_candidates
                    if candidate["tag_priority"] == preferred_priority
                ]

                selected_rows.append(
                    max(
                        preferred_candidates,
                        key=lambda candidate: (
                            candidate["source_filed"],
                            candidate["source_accession_number"],
                        ),
                    )
                )

    return selected_rows


def validate_staged_rows(rows: list[dict[str, Any]]) -> None:
    """Validate output completeness and uniqueness at the intended grain."""
    expected_keys = {
        (ticker, metric_name, fiscal_year)
        for ticker in COMPANIES
        for metric_name in REQUIRED_METRICS
        for fiscal_year in TARGET_FISCAL_YEARS
    }

    actual_keys = {
        (row["ticker"], row["metric_name"], row["fiscal_year"])
        for row in rows
    }

    missing_keys = sorted(expected_keys - actual_keys)
    unexpected_keys = sorted(actual_keys - expected_keys)

    if missing_keys or unexpected_keys:
        raise SystemExit(
            "Staged data did not match the expected company, metric, "
            f"and year combinations. Missing: {missing_keys}. "
            f"Unexpected: {unexpected_keys}."
        )

    if len(rows) != EXPECTED_STAGED_RECORD_COUNT:
        raise SystemExit(
            f"Expected {EXPECTED_STAGED_RECORD_COUNT} staged records, "
            f"but found {len(rows)}."
        )


def write_staged_data(rows: list[dict[str, Any]]) -> Path:
    """Write the standardized financial fact table."""
    STAGED_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    output_path = (
        STAGED_DATA_DIRECTORY / "financial_facts_2020_2025.csv"
    )

    fieldnames = [
        "ticker",
        "company_name",
        "cik",
        "metric_name",
        "fiscal_year",
        "value_usd",
        "unit",
        "period_start",
        "period_end",
        "source_form",
        "source_filed",
        "source_accession_number",
        "source_taxonomy",
        "source_xbrl_tag",
        "tag_priority",
        "source_file",
        "source_url",
        "source_file_sha256",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def write_transformation_manifest(
    run_directory: Path,
    staged_data_path: Path,
) -> Path:
    """Write a summary of the successful transformation."""
    manifest = {
        "source_extraction_run_id": run_directory.name,
        "target_fiscal_years": list(TARGET_FISCAL_YEARS),
        "required_metrics": list(REQUIRED_METRICS),
        "expected_record_count": EXPECTED_STAGED_RECORD_COUNT,
        "actual_record_count": EXPECTED_STAGED_RECORD_COUNT,
        "output_file": staged_data_path.name,
        "status": "completed",
    }

    output_path = (
        STAGED_DATA_DIRECTORY
        / "financial_facts_2020_2025_manifest.json"
    )
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    """Build the standardized staged financial dataset."""
    arguments = parse_arguments()
    run_directory = arguments.run_directory.resolve()
    source_metadata_by_ticker = load_source_metadata(run_directory)
    companyfacts_files = sorted(run_directory.glob("*_companyfacts.json"))
    candidates = []

    for file_path in companyfacts_files:
        ticker = file_path.name.split("_")[0]
        payload = json.loads(file_path.read_text(encoding="utf-8"))

        candidates.extend(
            collect_candidates(
                payload=payload,
                ticker=ticker,
                source_file=file_path,
                source_metadata=source_metadata_by_ticker[ticker],
            )
        )

    selected_rows = select_contract_facts(candidates)
    validate_staged_rows(selected_rows)

    selected_rows.sort(
        key=lambda row: (
            row["ticker"],
            row["metric_name"],
            row["fiscal_year"],
        )
    )

    staged_data_path = write_staged_data(selected_rows)
    manifest_path = write_transformation_manifest(
        run_directory=run_directory,
        staged_data_path=staged_data_path,
    )

    print(
        f"Created {len(selected_rows)} standardized financial records."
    )
    print(f"Staged data: {staged_data_path}")
    print(f"Transformation manifest: {manifest_path}")


if __name__ == "__main__":
    main()
