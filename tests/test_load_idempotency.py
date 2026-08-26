"""The idempotency test — the one interviewers care about.

Idempotent = running the load twice gives the same result as running it once.
Pipelines get retried all the time (a network blip, a crash, a manual re-run). If
a retry doubles your data, dashboards lie and trust is gone. So we PROVE the load
is idempotent: run it twice, assert the row count didn't budge.

We also show the opposite — a naive append-based load — failing the same check, so
you can see what non-idempotency actually looks like.
"""
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from pipeline.etl import load


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "customer": ["Ann", "Bo", "Cy"],
            "product": ["Widget", "Cog", "Gizmo"],
            "quantity": [2, 1, 5],
            "price": [10.0, 20.0, 4.0],
            "revenue": [20.0, 20.0, 20.0],
        }
    )


def test_load_is_idempotent(tmp_path: Path, sample_clean_df):
    """Run the real load twice into a temp DuckDB; row count must be identical."""
    db = tmp_path / "wh.duckdb"
    first = load(sample_clean_df, db, table="raw_sales")
    second = load(sample_clean_df, db, table="raw_sales")
    assert first == second == len(sample_clean_df)


def _naive_append_load(df: pd.DataFrame, db_path: Path, table: str) -> int:
    """A WRONG load that appends every run — kept here only to demonstrate the bug."""
    con = duckdb.connect(str(db_path))
    try:
        con.register("df_in", df)
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df_in WHERE 1=0")
        con.execute(f"INSERT INTO {table} SELECT * FROM df_in")
        (count,) = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    finally:
        con.close()
    return int(count)


def test_append_load_is_not_idempotent(tmp_path: Path, sample_clean_df):
    """The naive append load DOUBLES the data on the second run. This is the bug
    our real load avoids. We assert the bug exists, to make the contrast concrete.
    """
    db = tmp_path / "bad.duckdb"
    first = _naive_append_load(sample_clean_df, db, "raw_sales")
    second = _naive_append_load(sample_clean_df, db, "raw_sales")
    assert first == 3
    assert second == 6  # <- duplicated! not idempotent.
