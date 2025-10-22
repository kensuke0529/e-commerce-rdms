-- How many customers have made at least one purchase?
select count(distinct c.customer_id) as total_actual_users
from customer as c
join order_header as oh on c.customer_id = oh.customer_id;


-- Calculate customer lifetime value (CLV). Show top 10 customers by total spend.
select
	c.customer_id,
	c.first_name,
	c.last_name,
	sum(p.amount) as clv
from customer as c 
join order_header as oh on c.customer_id = oh.customer_id 
join payment as p on p.order_id = oh.order_id
group by c.customer_id
order by sum(p.amount) desc 
limit 10;

-- Perform RFM analysis (Recency, Frequency, Monetary). Segment customers into: Champions, Loyal, At-Risk, Lost.
-- 1. last day purchase
with recency_days as (
	select
		c.customer_id,
		c.first_name,
		c.last_name,
		current_date - max(oh.order_date) as days_since_last_order
	from order_header as  oh 
	join customer as c on oh.customer_id = c.customer_id 
	group by c.customer_id, c.first_name, c.last_name
)
select *
from recency_days 
order by days_since_last_order  

-- 2. how many orders 
select 
	customer_id,
	count(*) as total_purchase
from order_header
group by customer_id

-- 3. total_spending
select 
	oh.customer_id,
	sum(p.amount) as total_spending
from order_header as oh
join payment as p on oh.order_id = p.order_id
group by oh.customer_id 

-- Combined
select
	c.customer_id,
	c.first_name,
	c.last_name,
	current_date - max(oh.order_date) as days_since_last_order,
	count(*) as total_purchase,
	sum(p.amount) as total_spending,
	case 
		when sum(p.amount) < 500 then 'low'
		when sum(p.amount) < 2000 then 'mid'
		else 'high'
	end as spending_group
from order_header as  oh 
join customer as c on oh.customer_id = c.customer_id 
join payment as p on oh.order_id = p.order_id
group by c.customer_id, c.first_name, c.last_name
	
	
-- calculate customer retention rate by cohort (group by first purchase month, track repeat purchases)
-- 1. find each customer's first purchase date (their cohort)
with first_purchase as (
    select 
        customer_id,
        min(order_date) as cohort_month,
        date_trunc('month', min(order_date)) as cohort_month_start
    from order_header
    group by customer_id
),

-- 2. get all purchases with their cohort info
customer_orders as (
    select 
        o.customer_id,
        o.order_date,
        fp.cohort_month_start,
        -- calculate how many months after first purchase
        date_part('month', age(o.order_date, fp.cohort_month_start)) as months_since_first
    from order_header o
    join first_purchase fp on o.customer_id = fp.customer_id
),
-- 3. count unique customers per cohort per month
cohort_counts as (
    select 
        cohort_month_start,
        months_since_first,
        count(distinct customer_id) as active_customers
    from customer_orders
    group by cohort_month_start, months_since_first
),
cohort_size as (
    select 
        cohort_month_start,
        count(distinct customer_id) as cohort_size
    from first_purchase
    group by cohort_month_start
)
select 
    cc.cohort_month_start,
    cc.months_since_first,
    cc.active_customers,
    cs.cohort_size,
    round(100.0 * cc.active_customers / cs.cohort_size, 2) as retention_rate
from cohort_counts cc
join cohort_size cs on cc.cohort_month_start = cs.cohort_month_start
order by cc.cohort_month_start, cc.months_since_first;

-- Find customers who bid but never purchased. Calculate their total bid activity and potential lost revenue.
with purchased_customers as (
    select DISTINCT customer_id from order_header
)
select
    b.customer_id,
    c.first_name,
    c.last_name,
    count(DISTINCT b.bid_id) as total_bids,
    count(DISTINCT b.product_id) as products_bid_on,
    sum(b.bid_amount) as total_bid_value,
    max(b.bid_amount) as highest_bid,
    max(b.bid_date) as last_bid_date
from bid b
join customer c ON b.customer_id = c.customer_id
left join purchased_customers pc on b.customer_id = pc.customer_id
where pc.customer_id IS NULL
group by b.customer_id, c.first_name, c.last_name
order by total_bid_value desc;

