"""Inspect annual SEC fact values for candidate project metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_DIRECTORY = PROJECT_ROOT / "docs"
TARGET_FISCAL_YEARS = set(range(2020, 2026))

METRIC_CANDIDATES: dict[str, tuple[str, ...]] = {
    "revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
    ),
    "operating_income": (
        "OperatingIncomeLoss",
    ),
    "net_income": (
        "NetIncomeLoss",
        "ProfitLoss",
    ),
    "total_assets": (
        "Assets",
    ),
    "stockholders_equity": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
    "operating_cash_flow": (
        "NetCashProvidedByUsedInOperatingActivities",
    ),
    "capital_expenditures": (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquireOtherPropertyPlantAndEquipment",
        "PaymentsForProceedsFromOtherPropertyPlantAndEquipment",
    ),
}


def parse_arguments() -> argparse.Namespace:
    """Read the raw extraction directory to inspect."""
    parser = argparse.ArgumentParser(
        description="Inspect annual values for candidate SEC XBRL tags."
    )
    parser.add_argument(
        "--run-directory",
        required=True,
        type=Path,
        help="Directory containing downloaded *_companyfacts.json files.",
    )
    return parser.parse_args()


def analysis_fiscal_year(fact: dict[str, Any]) -> int | None:
    """Return the fiscal year represented by the fact's reporting end date."""
    period_end = fact.get("end", "")
    if not isinstance(period_end, str) or len(period_end) < 4:
        return None
    try:
        return int(period_end[:4])
    except ValueError:
        return None


def is_target_annual_fact(fact: dict[str, Any]) -> bool:
    """Return whether a fact is an annual 10 K value in the target period."""
    fiscal_year = analysis_fiscal_year(fact)
    return (
        fact.get("form", "").startswith("10-K")
        and fact.get("fp") == "FY"
        and fiscal_year in TARGET_FISCAL_YEARS
    )


def fact_sort_key(fact: dict[str, Any]) -> tuple[str, str]:
    """Prefer the most recently filed fact when duplicates exist."""
    return (
        str(fact.get("filed", "")),
        str(fact.get("accn", "")),
    )


def inspect_concept(
    ticker: str,
    entity_name: str,
    project_metric: str,
    xbrl_tag: str,
    concept: dict[str, Any],
) -> list[dict[str, str | int | float]]:
    """Return the latest annual fact for each target fiscal year."""
    selected_facts: dict[int, dict[str, Any]] = {}

    for unit, facts in concept["units"].items():
        if unit != "USD":
            continue

        for fact in facts:
            if not is_target_annual_fact(fact):
                continue

            fiscal_year = analysis_fiscal_year(fact)
            if fiscal_year is None:
                continue
            existing_fact = selected_facts.get(fiscal_year)

            if existing_fact is None or fact_sort_key(fact) > fact_sort_key(
                existing_fact
            ):
                selected_facts[fiscal_year] = fact

    rows = []

    for fiscal_year in sorted(selected_facts):
        fact = selected_facts[fiscal_year]

        rows.append(
            {
                "ticker": ticker,
                "entity_name": entity_name,
                "project_metric": project_metric,
                "xbrl_tag": xbrl_tag,
                "analysis_fiscal_year": fiscal_year,
                "filing_fiscal_year": fact.get("fy", ""),
                "period_start": fact.get("start", ""),
                "period_end": fact.get("end", ""),
                "value_usd": fact["val"],
                "filed": fact.get("filed", ""),
                "accession_number": fact.get("accn", ""),
                "form": fact.get("form", ""),
            }
        )

    return rows


def inspect_file(file_path: Path) -> list[dict[str, str | int | float]]:
    """Inspect all candidate metric tags for one company."""
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    ticker = file_path.name.split("_")[0]
    entity_name = payload["entityName"]
    us_gaap_concepts = payload["facts"].get("us-gaap", {})
    rows = []

    for project_metric, candidate_tags in METRIC_CANDIDATES.items():
        for xbrl_tag in candidate_tags:
            concept = us_gaap_concepts.get(xbrl_tag)

            if concept is None:
                continue

            rows.extend(
                inspect_concept(
                    ticker=ticker,
                    entity_name=entity_name,
                    project_metric=project_metric,
                    xbrl_tag=xbrl_tag,
                    concept=concept,
                )
            )

    return rows


def write_output(
    rows: list[dict[str, str | int | float]],
    run_directory: Path,
) -> Path:
    """Write candidate values for review."""
    DOCUMENTATION_DIRECTORY.mkdir(exist_ok=True)
    output_path = (
        DOCUMENTATION_DIRECTORY
        / f"annual_candidate_values_{run_directory.name}.csv"
    )

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main() -> None:
    """Inspect candidate facts for all project companies."""
    arguments = parse_arguments()
    run_directory = arguments.run_directory.resolve()
    companyfacts_files = sorted(run_directory.glob("*_companyfacts.json"))

    if not companyfacts_files:
        raise SystemExit(
            "No Company Facts files found in the provided run directory."
        )

    rows = []

    for file_path in companyfacts_files:
        rows.extend(inspect_file(file_path))

    if not rows:
        raise SystemExit("No annual candidate values found.")

    output_path = write_output(rows, run_directory)

    for ticker in sorted({row["ticker"] for row in rows}):
        ticker_rows = [row for row in rows if row["ticker"] == ticker]
        print(f"{ticker}: {len(ticker_rows)} candidate annual values")

    print(f"Candidate values saved: {output_path}")


if __name__ == "__main__":
    main()
