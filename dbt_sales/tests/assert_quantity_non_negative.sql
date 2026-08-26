-- A "singular" test: just a SELECT that returns the BAD rows. dbt passes the test
-- when this query returns ZERO rows. Use singular tests for one-off business rules
-- that the built-in generic tests (not_null, unique, accepted_values, relationships)
-- don't cover. Here: a sales quantity must never be negative.
select
    order_id,
    quantity
from {{ ref('stg_sales') }}
where quantity < 0
