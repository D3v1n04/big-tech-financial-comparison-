"""Download raw SEC Company Facts API responses for project companies."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "sec_companyfacts"

COMPANIES = {
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "cik": "0000789019",
    },
    "AMZN": {
        "company_name": "Amazon.com, Inc.",
        "cik": "0001018724",
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "cik": "0001652044",
    },
}


def build_companyfacts_url(cik: str) -> str:
    """Return the official SEC Company Facts API URL for one CIK."""
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def write_manifest(run_directory: Path, manifest: dict[str, Any]) -> None:
    """Save extraction metadata for auditability."""
    manifest_path = run_directory / "extraction_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def download_companyfacts(
    session: requests.Session,
    ticker: str,
    company: dict[str, str],
    run_directory: Path,
) -> dict[str, str]:
    """Download and save one company's original SEC API response."""
    cik = company["cik"]
    url = build_companyfacts_url(cik)

    response = session.get(url, timeout=30)
    response.raise_for_status()

    raw_content = response.content
    payload = response.json()
    output_path = run_directory / f"{ticker}_companyfacts.json"

    output_path.write_bytes(raw_content)

    return {
        "ticker": ticker,
        "company_name": company["company_name"],
        "api_entity_name": payload.get("entityName", ""),
        "cik": cik,
        "source_url": url,
        "output_file": output_path.name,
        "sha256": hashlib.sha256(raw_content).hexdigest(),
        "http_status": str(response.status_code),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def parse_arguments() -> argparse.Namespace:
    """Read command line settings."""
    parser = argparse.ArgumentParser(
        description="Download SEC Company Facts data for Big Tech comparison."
    )
    parser.add_argument(
        "--user-agent",
        required=True,
        help="Contact identification required by the SEC, such as "
        "'Devin Lee devin@example.com'.",
    )
    return parser.parse_args()


def main() -> None:
    """Download SEC data for all project companies."""
    arguments = parse_arguments()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_directory = RAW_DATA_DIRECTORY / run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "source": "SEC EDGAR Company Facts API",
        "status": "in_progress",
        "files": [],
    }

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": arguments.user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
    )

    try:
        for index, (ticker, company) in enumerate(COMPANIES.items()):
            print(f"Downloading {ticker}...")
            file_record = download_companyfacts(
                session=session,
                ticker=ticker,
                company=company,
                run_directory=run_directory,
            )
            manifest["files"].append(file_record)

            if index < len(COMPANIES) - 1:
                time.sleep(0.2)

    except requests.RequestException as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        write_manifest(run_directory, manifest)
        raise SystemExit(f"SEC extraction failed: {error}") from error

    manifest["status"] = "completed"
    write_manifest(run_directory, manifest)

    print(f"Extraction completed: {run_directory}")


if __name__ == "__main__":
    main()
