-- Mart model: the business-facing answer. Marts join and aggregate staging models
-- into something a dashboard or analyst actually queries. This one rolls revenue
-- up by product.

with sales as (
    select * from {{ ref('stg_sales') }}
)

select
    product,
    count(*) as n_orders,
    sum(quantity) as units_sold,
    round(sum(revenue), 2) as total_revenue,
    round(avg(revenue), 2) as avg_order_revenue
from sales
group by product
order by total_revenue desc
