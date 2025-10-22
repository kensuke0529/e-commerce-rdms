-- Total Revenue
select sum(p.amount) as total_revenue
from payment as p 
join order_header as h on p.order_id  = h.order_id; 

-- Monthly revenue trend
with months as (
select 
	extract(year from h.order_date) as year,
	extract(month from h.order_date) as month, 
	*
from payment as p 
join order_header as h on p.order_id  = h.order_id
) 
select 
	year,
	month,
	sum(amount) as total_revenue,
	count(*) as order_count,
	round(avg(amount),2) as avg_order_value
from months
group by year, month
order by year, month;

-- month-over-month revenue growth %
with months as (
    select 
        extract(year FROM h.order_date) as year,
        extract(month FROM h.order_date) as month,
        p.amount
    from payment as p
    join order_header as h ON p.order_id = h.order_id
),
revenue_by_month as (
    select
        year,
        month,
        SUM(amount) as monthly_revenue
    from months
    group by year, month
),
rags as (
    select
        year,
        month,
        monthly_revenue,
        LAG(monthly_revenue) over (ORDER BY year, month) as lag_month
    from revenue_by_month
)
select 
    year,
    month,
    ROUND(( (monthly_revenue - lag_month) / NULLIF(lag_month, 0) ) * 100,2) AS growth_percent
from rags
order by year, month;

-- category revenue
select 
	pr.category,
	sum(p.amount) as total_revenue,
	round(sum(p.amount) / 
		(
		select sum(amount) as total_revenue
		from payment
		) * 100,2) as per_cat_revenue
from payment as p 
join order_header as h on p.order_id  = h.order_id
join product as pr on h.product_id =pr.product_id 
group by pr.category
order by per_cat_revenue desc;

-- Calculate revenue per seller with 10% platform fee deduction. Rank sellers by net revenue and identify top 20% performers.
select 
    s.seller_id,
    round(sum(p.amount),2) as total_revenue,
    round(sum(p.amount) * 0.9,2) as net_revenue,
    rank() over (order by sum(p.amount) * 0.9 desc) as rank
from payment as p 
join order_header as h on p.order_id  = h.order_id
join product as pr on h.product_id =pr.product_id 
join seller as s on pr.seller_id = s.seller_id
group by s.seller_id
order by total_revenue desc
limit 5;


