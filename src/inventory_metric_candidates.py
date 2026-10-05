"""Inventory candidate SEC XBRL tags for project financial metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_DIRECTORY = PROJECT_ROOT / "docs"

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
        description="Inventory candidate SEC XBRL tags in raw Company Facts data."
    )
    parser.add_argument(
        "--run-directory",
        required=True,
        type=Path,
        help="Directory containing downloaded *_companyfacts.json files.",
    )
    return parser.parse_args()


def count_annual_observations(concept: dict[str, Any]) -> int:
    """Count annual 10 K observations for one XBRL concept."""
    count = 0

    for facts in concept["units"].values():
        for fact in facts:
            if fact.get("form", "").startswith("10-K") and fact.get("fp") == "FY":
                count += 1

    return count


def inventory_file(file_path: Path) -> list[dict[str, str | int]]:
    """Return available candidate tags for one company file."""
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    us_gaap_concepts = payload["facts"].get("us-gaap", {})
    ticker = file_path.name.split("_")[0]
    rows: list[dict[str, str | int]] = []

    for metric_name, candidate_tags in METRIC_CANDIDATES.items():
        for tag_name in candidate_tags:
            concept = us_gaap_concepts.get(tag_name)

            if concept is None:
                continue

            rows.append(
                {
                    "ticker": ticker,
                    "entity_name": payload["entityName"],
                    "project_metric": metric_name,
                    "xbrl_taxonomy": "us-gaap",
                    "xbrl_tag": tag_name,
                    "label": concept.get("label", ""),
                    "units": ", ".join(sorted(concept["units"].keys())),
                    "annual_10k_observation_count": count_annual_observations(
                        concept
                    ),
                }
            )

    return rows


def write_inventory(
    inventory_rows: list[dict[str, str | int]],
    run_directory: Path,
) -> Path:
    """Write the candidate tag inventory as project documentation."""
    DOCUMENTATION_DIRECTORY.mkdir(exist_ok=True)
    output_path = (
        DOCUMENTATION_DIRECTORY
        / f"metric_candidate_inventory_{run_directory.name}.csv"
    )

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=list(inventory_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(inventory_rows)

    return output_path


def main() -> None:
    """Inspect all raw Company Facts files in one extraction run."""
    arguments = parse_arguments()
    run_directory = arguments.run_directory.resolve()
    companyfacts_files = sorted(run_directory.glob("*_companyfacts.json"))

    if not companyfacts_files:
        raise SystemExit(
            "No Company Facts files found in the provided run directory."
        )

    inventory_rows = []

    for file_path in companyfacts_files:
        inventory_rows.extend(inventory_file(file_path))

    for row in inventory_rows:
        print(
            f"{row['ticker']} | {row['project_metric']} | "
            f"{row['xbrl_tag']} | "
            f"{row['annual_10k_observation_count']} annual observations"
        )

    output_path = write_inventory(inventory_rows, run_directory)
    print(f"Inventory saved: {output_path}")


if __name__ == "__main__":
    main()
