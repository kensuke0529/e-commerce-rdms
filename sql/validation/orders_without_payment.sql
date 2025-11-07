-- orders wo payment 
select count(*) as orders_without_payment
from order_header as oh 
left join  payment as p on oh.order_id = p.order_id 
where p.payment_id is null;