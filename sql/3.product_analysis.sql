-- 1. List top 10 best-selling products by quantity sold.
select 
	p.product_id,
	p.product_name,
	count(*) as total_sold
from product as p 
join order_header as oh on p.product_id = oh.product_id 
group by p.product_id 
order by total_sold desc
limit 10;

-- 2. Which products have the highest average customer rating? (minimum 3 reviews)
select 
	p.product_id,
	p.product_name,
	count(*) as total_sold, 
	avg(cr.rating) as avg_rating
from product as p 
join customer_review as cr  on p.product_id = cr.product_id 
group by p.product_id
having avg(cr.rating) > 3 and count(*) > 3
order by avg_rating desc;

-- 3. Product performance dashboard - units sold, revenue, average rating, review count, bid activity (total bids, unique bidders).
select 
	p.product_id,
	p.product_name,
	count(*) as total_sold, 
	avg(cr.rating) as avg_rating,
	sum(pa.amount) as revenue,
	count(cr.review_id) as review_count,
	count(b.bid_id) as total_bids,
	count(distinct b.bid_id) as unique_bidders
from product as p 
join order_header as oh on p.product_id = oh.product_id 
join customer_review as cr  on p.product_id = cr.product_id 
join payment as pa on pa.order_id = oh.order_id 
join bid as b on cr.product_id = b.product_id
group by p.product_id;

-- 4. Identify slow-moving inventory (products with less than 2 units sold).
select 
	p.product_id,
	p.product_name,
	count(*) as total_sold
from product as p 
join order_header as oh on p.product_id = oh.product_id 
group by p.product_id
having count(*) < 2;
