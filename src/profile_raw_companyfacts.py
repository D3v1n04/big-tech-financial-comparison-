"""Profile raw SEC Company Facts API responses."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_DIRECTORY = PROJECT_ROOT / "docs"


def parse_arguments() -> argparse.Namespace:
    """Read the raw extraction directory to profile."""
    parser = argparse.ArgumentParser(
        description="Profile raw SEC Company Facts files from one extraction run."
    )
    parser.add_argument(
        "--run-directory",
        required=True,
        type=Path,
        help="Directory containing downloaded *_companyfacts.json files.",
    )
    return parser.parse_args()


def iter_facts(payload: dict[str, Any]):
    """Yield every XBRL fact observation from a Company Facts response."""
    for taxonomy_name, concepts in payload["facts"].items():
        for concept_name, concept_data in concepts.items():
            for unit_name, facts in concept_data["units"].items():
                for fact in facts:
                    yield taxonomy_name, concept_name, unit_name, fact


def profile_companyfacts_file(file_path: Path) -> dict[str, str | int]:
    """Return summary information for one raw Company Facts JSON file."""
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    concept_count = sum(
        len(concepts)
        for concepts in payload["facts"].values()
    )
    fact_observation_count = 0
    annual_fiscal_years: set[int] = set()

    for _, _, _, fact in iter_facts(payload):
        fact_observation_count += 1

        form = fact.get("form", "")
        fiscal_period = fact.get("fp")
        fiscal_year = fact.get("fy")

        if (
            form.startswith("10-K")
            and fiscal_period == "FY"
            and isinstance(fiscal_year, int)
        ):
            annual_fiscal_years.add(fiscal_year)

    annual_year_list = sorted(annual_fiscal_years)

    return {
        "ticker": file_path.name.split("_")[0],
        "entity_name": payload["entityName"],
        "cik": str(payload["cik"]),
        "taxonomy_count": len(payload["facts"]),
        "concept_count": concept_count,
        "fact_observation_count": fact_observation_count,
        "earliest_annual_fiscal_year": (
            annual_year_list[0] if annual_year_list else ""
        ),
        "latest_annual_fiscal_year": (
            annual_year_list[-1] if annual_year_list else ""
        ),
        "annual_fiscal_year_count": len(annual_year_list),
        "source_file": file_path.name,
    }


def write_profile(
    profile_rows: list[dict[str, str | int]],
    run_directory: Path,
) -> Path:
    """Write the profile as a reusable CSV documentation artifact."""
    DOCUMENTATION_DIRECTORY.mkdir(exist_ok=True)
    output_path = (
        DOCUMENTATION_DIRECTORY
        / f"raw_data_profile_{run_directory.name}.csv"
    )

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=list(profile_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(profile_rows)

    return output_path


def main() -> None:
    """Profile every downloaded company response in one extraction run."""
    arguments = parse_arguments()
    run_directory = arguments.run_directory.resolve()

    if not run_directory.is_dir():
        raise SystemExit(f"Run directory does not exist: {run_directory}")

    companyfacts_files = sorted(
        run_directory.glob("*_companyfacts.json")
    )

    if not companyfacts_files:
        raise SystemExit(
            "No Company Facts files found in the provided run directory."
        )

    profile_rows = [
        profile_companyfacts_file(file_path)
        for file_path in companyfacts_files
    ]

    for row in profile_rows:
        print(
            f"{row['ticker']}: "
            f"{row['concept_count']:,} concepts, "
            f"{row['fact_observation_count']:,} fact observations, "
            f"annual FY {row['earliest_annual_fiscal_year']} "
            f"to {row['latest_annual_fiscal_year']}"
        )

    output_path = write_profile(profile_rows, run_directory)
    print(f"Profile saved: {output_path}")


if __name__ == "__main__":
    main()
