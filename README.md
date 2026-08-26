# Sales pipeline with CI/CD

<!-- After you push to GitHub, swap YOURNAME/REPO below and the badge goes live. -->
![CI](https://github.com/YOURNAME/REPO/actions/workflows/ci.yml/badge.svg)

A small but complete data pipeline that is **protected by CI/CD**. Every change is
automatically linted, tested, and built before it can merge; once merged, the dbt
documentation is published to GitHub Pages. The pipeline itself is deliberately
simple so the *engineering discipline around it* is the star.

## What it does

```
data/raw/sales.csv
      │  EXTRACT (pandas)
      ▼
  clean + derive revenue        ← pure functions in pipeline/transform.py (unit-tested)
      │  LOAD (idempotent)
      ▼
warehouse.duckdb : raw_sales    ← a zero-setup local analytics database
      │  dbt
      ▼
stg_sales (view) → sales_by_product (table)   ← modelled + data-tested with dbt
```

## The CI/CD part (the point of the project)

On every pull request and push to `main`, `.github/workflows/ci.yml` runs four gates
on a clean cloud runner. If any fails, the change is blocked:

1. **`sqlfluff lint`**: the SQL must meet the style rules in `.sqlfluff`.
2. **`pytest`**: the Python transforms must be correct, including an **idempotency
   test** that loads twice and asserts the row count doesn't change.
3. **ETL run**: `python -m pipeline.etl` builds the warehouse.
4. **`dbt build`**: the models must build and all dbt data tests must pass.

On push to `main`, `.github/workflows/deploy.yml` (the "CD" half) builds the dbt docs
and deploys them to **GitHub Pages**.

## Run it locally

You're on Windows, so these are PowerShell commands.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt

# (optional) regenerate a bigger, messier sample dataset
python scripts\generate_data.py

# run the EXACT checks CI runs, in order, stopping at the first failure:
python scripts\run_checks.py
```

If `run_checks.py` ends with **"All checks passed"**, a push will be green on GitHub.

You can also run each gate by hand:

```powershell
sqlfluff lint dbt_sales/models
pytest
python -m pipeline.etl
dbt build --project-dir dbt_sales --profiles-dir dbt_sales
```

## Layout

```
├── pipeline/                  the ETL
│   ├── transform.py           pure, unit-tested clean/derive functions
│   └── etl.py                 extract from CSV, idempotent load into DuckDB
├── tests/                     pytest suite
│   ├── test_transform.py      correctness of the transforms
│   └── test_load_idempotency.py   proves the load is idempotent (and shows a non-idempotent load failing)
├── dbt_sales/                 the dbt project (DuckDB)
│   ├── models/staging/        stg_sales + source declaration + tests
│   ├── models/marts/          sales_by_product + tests
│   └── tests/                 a singular (custom) data test
├── scripts/
│   ├── generate_data.py       make a messy sample CSV (seeded, deterministic)
│   └── run_checks.py          run all CI gates locally
├── .github/workflows/
│   ├── ci.yml                 the CI: lint + test + build on every PR
│   └── deploy.yml             the CD: publish dbt docs to GitHub Pages
├── .sqlfluff                  SQL lint rules
├── requirements.txt           pinned dependencies
└── .env.example               template for secrets (real .env is git-ignored)
```

## Deploying / hosting it

See **`HOSTING.md`** for step-by-step: pushing to GitHub, turning on Actions,
enabling Pages for the docs, adding the status badge, and protecting `main` so red
builds can't merge.

## Why DuckDB and not Postgres/Snowflake?

So the whole thing runs for free with zero setup, on your laptop and on a CI runner,
with nothing but `pip install`. The patterns (idempotent load, staging→marts, data
tests, CI gates) are identical to what you'd do against Postgres, BigQuery, or
Snowflake; only the connection string changes. Swapping the warehouse is a deliberate
later exercise, not a rewrite.
