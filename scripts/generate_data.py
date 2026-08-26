"""Generate a messy sales CSV to practise on.

Real raw data is messy on purpose: mixed date formats, stray whitespace, missing
values, duplicates. Handling that mess IS the job, so we manufacture it here. The
seed is fixed so the output is identical every run — which keeps the tests and the
dbt build deterministic in CI.

Run:  python scripts/generate_data.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from faker import Faker

OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "sales.csv"
PRODUCTS = ["Widget", "Gadget", "Sprocket", "Cog", "Gizmo"]
N_ROWS = 200
SEED = 42


def main() -> None:
    fake = Faker()
    Faker.seed(SEED)
    random.seed(SEED)

    rows = []
    for i in range(1, N_ROWS + 1):
        order_id = 1000 + i
        customer = f"  {fake.name()}  " if i % 7 == 0 else fake.name()  # stray whitespace sometimes
        product = random.choice(PRODUCTS)

        # mixed date formats on purpose
        d = fake.date_between(start_date="-1y", end_date="today")
        if i % 3 == 0:
            order_date = d.strftime("%Y-%m-%d")
        elif i % 3 == 1:
            order_date = d.strftime("%m/%d/%Y")
        else:
            order_date = d.strftime("%d-%b-%Y")

        quantity = "" if i % 11 == 0 else random.randint(1, 10)   # some missing quantities
        price = "" if i % 13 == 0 else round(random.uniform(5, 200), 2)  # some missing prices

        rows.append([order_id, customer, product, order_date, quantity, price])

    # inject a handful of exact-duplicate orders to prove de-duplication works
    for dup in rows[:5]:
        rows.append(list(dup))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer", "product", "order_date", "quantity", "price"])
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows (incl. duplicates + injected mess) to {OUT}")


if __name__ == "__main__":
    main()
