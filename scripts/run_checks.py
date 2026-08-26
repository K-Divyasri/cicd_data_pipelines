"""Run the SAME checks locally that GitHub Actions runs in CI.

The golden rule of CI: if this passes on your machine, it should pass on GitHub.
So run this before you push. It executes each gate in order and STOPS at the first
failure with a non-zero exit code — exactly like the CI workflow does.

Gates, in order:
  1. sqlfluff lint   — is the SQL clean?
  2. pytest          — is the Python correct (incl. the idempotency test)?
  3. build warehouse — run the ETL so dbt has data to build on
  4. dbt build       — do the models build and all data tests pass?

Run:  python scripts/run_checks.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BUILD_ROOT = Path(__file__).resolve().parent.parent

# (label, command). Commands run from the build/ root.
CHECKS = [
    ("Lint SQL (sqlfluff)", ["sqlfluff", "lint", "dbt_sales/models"]),
    ("Unit tests (pytest)", ["pytest"]),
    ("Run ETL (build warehouse.duckdb)", [sys.executable, "-m", "pipeline.etl"]),
    ("Build + test models (dbt)", ["dbt", "build", "--project-dir", "dbt_sales", "--profiles-dir", "dbt_sales"]),
]


def run() -> int:
    for label, cmd in CHECKS:
        print(f"\n{'=' * 70}\n>>> {label}\n    $ {' '.join(cmd)}\n{'=' * 70}")
        result = subprocess.run(cmd, cwd=BUILD_ROOT)
        if result.returncode != 0:
            print(f"\nFAILED at: {label} (exit code {result.returncode})")
            print("Fix this before pushing — CI would fail here too.")
            return result.returncode
    print("\nAll checks passed. Safe to push. CI should be green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
