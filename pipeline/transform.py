"""The TRANSFORM stage — pure functions only.

"Pure" means: takes a DataFrame, returns a DataFrame, touches no database, no
files, no network, no clock. That property is why these functions are trivial to
test in CI — a test just hands in a tiny DataFrame and checks what comes back.

Every public function here has matching tests in ../tests/test_transform.py.
If you change the behaviour, a test should change with it. That's the deal.
"""
from __future__ import annotations

import pandas as pd

EXPECTED_RAW_COLUMNS = ["order_id", "customer", "product", "order_date", "quantity", "price"]


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw sales DataFrame.

    Steps, each defending against a specific kind of mess found in real CSVs:
      1. trim stray whitespace in text columns
      2. parse the date column (mixed formats are common) into real datetimes
      3. coerce quantity/price to numbers; blanks become NaN
      4. quantity NaN -> 0 (assume none ordered); price NaN -> drop the row
         (a sale with no price is unusable)
      5. drop exact duplicate orders by order_id (keep first)

    Returns a new DataFrame; the input is not mutated.
    """
    missing = [c for c in EXPECTED_RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"raw data is missing required columns: {missing}")

    out = df.copy()

    # 1. whitespace
    for col in ("customer", "product"):
        out[col] = out[col].astype("string").str.strip()

    # 2. dates (format="mixed" lets pandas handle inconsistent inputs)
    out["order_date"] = pd.to_datetime(out["order_date"], format="mixed", errors="coerce")

    # 3. numeric coercion
    out["quantity"] = pd.to_numeric(out["quantity"], errors="coerce")
    out["price"] = pd.to_numeric(out["price"], errors="coerce")

    # 4. missing values
    out["quantity"] = out["quantity"].fillna(0).astype(int)
    out = out.dropna(subset=["price"])

    # 5. de-duplicate on the business key
    out = out.drop_duplicates(subset=["order_id"], keep="first")

    return out.reset_index(drop=True)


def add_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Derive revenue = quantity * price, rounded to 2 dp. Returns a new frame."""
    out = df.copy()
    out["revenue"] = (out["quantity"] * out["price"]).round(2)
    return out


def run_transform(df: pd.DataFrame) -> pd.DataFrame:
    """The full transform stage: clean, then derive revenue.

    This is the single entry point the ETL (and the tests) call.
    """
    return add_revenue(clean_sales(df))
