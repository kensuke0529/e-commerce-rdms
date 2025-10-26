select 
    oh.quantity, 
    p.product_price,
    oh.quantity * p.product_price as calculated_total, 
    pay.amount as actual_payment,
    pay.amount - (oh.quantity * p.product_price) as difference
from order_header as oh 
join product as p on oh.product_id = p.product_id 
join payment as pay on pay.order_id = oh.order_id