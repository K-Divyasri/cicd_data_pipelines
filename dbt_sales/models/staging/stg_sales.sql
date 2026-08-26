-- Staging model: one light pass over the raw source.
-- Staging models rename/cast/lightly-clean. They don't join or aggregate — that's
-- the marts' job. One staging model per source table is the usual convention.

with source as (
    select * from {{ source('raw', 'raw_sales') }}
)

select
    cast(order_id as integer) as order_id,
    customer,
    product,
    cast(order_date as date) as order_date,
    cast(quantity as integer) as quantity,
    cast(price as double) as price,
    cast(revenue as double) as revenue
from source
