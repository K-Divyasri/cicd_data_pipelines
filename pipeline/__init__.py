"""sales_pipeline — a small, well-tested ETL that CI/CD protects.

The package is split deliberately:
  transform.py  pure functions (no I/O) — the easy-to-test heart of the pipeline
  etl.py        the extract/load wiring around those functions

Keeping the transform logic pure (data in, data out, no database, no files) is
what makes it cheap to test in CI. That separation is the whole trick.
"""
from .transform import clean_sales, add_revenue, run_transform

__all__ = ["clean_sales", "add_revenue", "run_transform"]
