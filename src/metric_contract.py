"""Canonical metric definitions for the Big Tech financial comparison."""

TARGET_FISCAL_YEARS = tuple(range(2020, 2026))

COMPANIES = {
    "AMZN": {
        "company_name": "Amazon.com, Inc.",
        "cik": "0001018724",
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "cik": "0001652044",
    },
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "cik": "0000789019",
    },
}

REQUIRED_METRICS = (
    "revenue",
    "operating_income",
    "net_income",
    "total_assets",
    "stockholders_equity",
    "operating_cash_flow",
    "capital_expenditures",
)

METRIC_TAG_PRIORITY = {
    "AMZN": {
        "revenue": (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
        ),
        "operating_income": (
            "OperatingIncomeLoss",
        ),
        "net_income": (
            "NetIncomeLoss",
        ),
        "total_assets": (
            "Assets",
        ),
        "stockholders_equity": (
            "StockholdersEquity",
        ),
        "operating_cash_flow": (
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        "capital_expenditures": (
            "PaymentsToAcquireProductiveAssets",
        ),
    },
    "GOOGL": {
        "revenue": (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
        ),
        "operating_income": (
            "OperatingIncomeLoss",
        ),
        "net_income": (
            "NetIncomeLoss",
        ),
        "total_assets": (
            "Assets",
        ),
        "stockholders_equity": (
            "StockholdersEquity",
        ),
        "operating_cash_flow": (
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        "capital_expenditures": (
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ),
    },
    "MSFT": {
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
        ),
        "total_assets": (
            "Assets",
        ),
        "stockholders_equity": (
            "StockholdersEquity",
        ),
        "operating_cash_flow": (
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        "capital_expenditures": (
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ),
    },
}

EXPECTED_STAGED_RECORD_COUNT = (
    len(COMPANIES)
    * len(REQUIRED_METRICS)
    * len(TARGET_FISCAL_YEARS)
)
