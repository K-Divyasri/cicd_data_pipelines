"""The EXTRACT and LOAD stages, wrapped around the pure transform.

We load into a local DuckDB file (`warehouse.duckdb`). DuckDB is a zero-setup
analytics database — no server, no account, just a file. That's deliberate: it
means CI can run the whole pipeline on a clean cloud runner with nothing but
`pip install`, and dbt reads the very same file afterwards.

The load is IDEMPOTENT: it replaces the table contents each run, so running the
pipeline twice never duplicates rows. There's a test that proves this
(test_load_is_idempotent). Idempotency is the property interviewers ask about.

Run it:  python -m pipeline.etl
"""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import duckdb
import pandas as pd

from .transform import run_transform

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("etl")

# Paths are relative to the build/ folder so the project is self-contained.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_ROOT / "data" / "raw" / "sales.csv"
DEFAULT_DB = PROJECT_ROOT / "warehouse.duckdb"
RAW_TABLE = "raw_sales"


def extract(csv_path: Path) -> pd.DataFrame:
    log.info("Extract: reading %s", csv_path)
    df = pd.read_csv(csv_path)
    log.info("Extract: %d raw rows", len(df))
    return df


def load(df: pd.DataFrame, db_path: Path, table: str = RAW_TABLE) -> int:
    """Replace `table` in the DuckDB file with `df`. Returns the loaded row count.

    CREATE OR REPLACE is what makes this idempotent — the table is rebuilt from
    scratch every run, so reruns can't accumulate duplicates.
    """
    log.info("Load: writing %d rows to %s::%s", len(df), db_path, table)
    con = duckdb.connect(str(db_path))
    try:
        # register the DataFrame so DuckDB can read it as a virtual table
        con.register("df_in", df)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df_in")
        (count,) = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    finally:
        con.close()
    log.info("Load: table %s now has %d rows", table, count)
    return int(count)


def run(csv_path: Path = DEFAULT_CSV, db_path: Path = DEFAULT_DB) -> int:
    raw = extract(csv_path)
    clean = run_transform(raw)
    rows = load(clean, db_path)
    log.info("Done. %d clean rows in %s::%s", rows, db_path, RAW_TABLE)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Sales CSV -> DuckDB ETL")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="input CSV path")
    parser.add_argument("--db", default=str(os.getenv("WAREHOUSE_DB", DEFAULT_DB)), help="DuckDB file path")
    args = parser.parse_args()
    run(Path(args.csv), Path(args.db))


if __name__ == "__main__":
    main()
