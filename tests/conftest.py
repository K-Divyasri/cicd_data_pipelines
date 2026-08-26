"""Shared pytest fixtures.

A fixture is reusable setup that tests ask for by naming it as an argument.
`raw_df` here is a tiny, deliberately messy sales DataFrame — the same kinds of
problems the real CSV has, but small enough to reason about by hand. Several
tests share it instead of each building their own.
"""
import pandas as pd
import pytest


@pytest.fixture
def raw_df() -> pd.DataFrame:
    """A small raw sales frame containing every mess the cleaner must handle:
    whitespace, mixed date formats, a missing quantity, a missing price, and a
    duplicate order_id.
    """
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 2],          # order 2 is duplicated
            "customer": ["  Ann  ", "Bo", "Cy", "Di", "Bo"],  # whitespace on Ann
            "product": ["Widget", "Cog", "Gizmo", "Widget", "Cog"],
            "order_date": ["2025-01-01", "01/02/2025", "03-Jan-2025", "2025-01-04", "01/02/2025"],
            "quantity": [2, None, 5, 1, None],    # one missing quantity
            "price": [10.0, 5.5, None, 20.0, 5.5],  # order 3 has no price -> dropped
        }
    )
