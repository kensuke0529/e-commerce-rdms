-- 1. Find data quality issues - orders without payment, products without seller, missing emails.
-- orders wo payment 
select count(*)
from order_header as oh 
left join  payment as p on oh.order_id = p.order_id 
where p.payment_id is null;

-- product wo seller
select count(*)
from product as p
left join seller as s on s.seller_id = p.seller_id 
where p.seller_id is null;

-- missing email
select count(*)
from app_user 
where email is null;

-- Duplicate emails
select email, count(*) AS occurrences
from app_user
group BY email
having count(*) > 1;

-- payment has to be more than quantity * product_price 
select 
    oh.quantity, 
    p.product_price,
    oh.quantity * p.product_price as calculated_total, 
    pay.amount as actual_payment,
    pay.amount - (oh.quantity * p.product_price) as difference
from order_header as oh 
join product as p on oh.product_id = p.product_id 
join payment as pay on pay.order_id = oh.order_id