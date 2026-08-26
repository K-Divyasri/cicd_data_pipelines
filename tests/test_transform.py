"""Tests for the pure transform functions.

Each test maps to a real failure it would catch in production. Read the
docstrings — they're the point, not decoration. Run them with:  pytest
"""
import pandas as pd
import pytest

from pipeline.transform import add_revenue, clean_sales, run_transform


def test_clean_strips_whitespace(raw_df):
    """Catches: leading/trailing spaces making "  Ann  " != "Ann" in joins/group-bys."""
    out = clean_sales(raw_df)
    assert "Ann" in set(out["customer"])
    assert "  Ann  " not in set(out["customer"])


def test_clean_parses_mixed_date_formats(raw_df):
    """Catches: dates left as strings, so you can't sort or filter by time."""
    out = clean_sales(raw_df)
    assert pd.api.types.is_datetime64_any_dtype(out["order_date"])
    # order 1's "2025-01-01" must parse to the 1st of January 2025
    row1 = out.loc[out["order_id"] == 1, "order_date"].iloc[0]
    assert (row1.year, row1.month, row1.day) == (2025, 1, 1)


def test_clean_drops_rows_with_missing_price(raw_df):
    """Catches: revenue silently computed as NaN because price was blank."""
    out = clean_sales(raw_df)
    # order_id 3 had a missing price -> must be gone
    assert 3 not in set(out["order_id"])


def test_clean_fills_missing_quantity_with_zero(raw_df):
    """Catches: a missing quantity blowing up the revenue multiplication."""
    out = clean_sales(raw_df)
    assert out["quantity"].isna().sum() == 0
    assert pd.api.types.is_integer_dtype(out["quantity"])


def test_clean_removes_duplicate_orders(raw_df):
    """Catches: the same order counted twice -> inflated totals. Order 2 was dup'd."""
    out = clean_sales(raw_df)
    assert out["order_id"].is_unique


def test_clean_does_not_mutate_input(raw_df):
    """Catches: a 'pure' function secretly editing its caller's data."""
    before = raw_df.copy()
    _ = clean_sales(raw_df)
    pd.testing.assert_frame_equal(raw_df, before)


def test_add_revenue_math():
    """Catches: a wrong revenue formula."""
    df = pd.DataFrame({"quantity": [2, 3], "price": [10.0, 4.5]})
    out = add_revenue(df)
    assert list(out["revenue"]) == [20.0, 13.5]


def test_missing_required_column_raises():
    """Catches: schema drift — a source column vanished/renamed upstream."""
    bad = pd.DataFrame({"order_id": [1]})  # missing everything else
    with pytest.raises(ValueError, match="missing required columns"):
        clean_sales(bad)


@pytest.mark.parametrize(
    "qty,price,expected",
    [(1, 100.0, 100.0), (0, 50.0, 0.0), (3, 19.99, 59.97)],
)
def test_revenue_parametrized(qty, price, expected):
    """Same logic, several cases at once — that's what parametrize buys you."""
    df = pd.DataFrame({"quantity": [qty], "price": [price]})
    assert add_revenue(df)["revenue"].iloc[0] == expected


def test_full_transform_output_schema(raw_df):
    """Catches: the final table not having the columns downstream/dbt expects."""
    out = run_transform(raw_df)
    expected_cols = {"order_id", "customer", "product", "order_date", "quantity", "price", "revenue"}
    assert set(out.columns) == expected_cols
