CREATE TABLE IF NOT EXISTS financial_facts (
    ticker text NOT NULL,
    company_name text NOT NULL,
    cik text NOT NULL,
    metric_name text NOT NULL,
    fiscal_year smallint NOT NULL,
    value_usd numeric(20, 0) NOT NULL,
    unit text NOT NULL,
    period_start date,
    period_end date NOT NULL,
    source_form text NOT NULL,
    source_filed date NOT NULL,
    source_accession_number text NOT NULL,
    source_taxonomy text NOT NULL,
    source_xbrl_tag text NOT NULL,
    tag_priority smallint NOT NULL,
    source_file text NOT NULL,
    source_url text NOT NULL,
    source_file_sha256 text NOT NULL,
    CONSTRAINT financial_facts_pk
        PRIMARY KEY (ticker, metric_name, fiscal_year)
);
