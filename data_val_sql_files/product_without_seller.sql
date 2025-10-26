-- product wo seller
select count(*)
from product as p
left join seller as s on s.seller_id = p.seller_id 
where p.seller_id is null;
