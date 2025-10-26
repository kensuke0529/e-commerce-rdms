-- Average shipping time (days) by carrier.
WITH duration AS (
  SELECT 
      s.shipping_id,
      s.carrier,
      ed.delivered_date,
      id.received_date,
      ed.delivered_date - id.received_date AS shipping_dates
  FROM shipping s
  LEFT JOIN export_distribution ed ON s.shipping_id = ed.shipping_id
  LEFT JOIN import_distribution id ON s.shipping_id = id.shipping_id
)
SELECT 
    carrier,
    AVG(shipping_dates) AS avg_shipping_duration,
    COUNT(*) AS total_shipping
FROM duration
GROUP BY carrier
order by avg_shipping_duration asc;


 -- Customer service metrics dashboard: total tickets, average resolution time, tickets by customer segment (CLV tier).
select 
	count(*) as total_ticket,
	round(avg(cs.duration_hours),2) as avg_service_hour
from customer_service as cs 
join staff as s on cs.staff_id = s.staff_id 


-- Orders with shipping delays (not shipped within 3 days). Correlate with customer review scores.
-- Group products by shipping speed and show rating distribution
WITH product_shipping AS (
    SELECT 
        oh.product_id,
        AVG(EXTRACT(DAY FROM (ed.delivered_date - id.received_date))) AS avg_shipping_days
    FROM order_header oh
    JOIN shipping s ON oh.shipping_id = s.shipping_id
    LEFT JOIN export_distribution ed ON s.shipping_id = ed.shipping_id
    LEFT JOIN import_distribution id ON s.shipping_id = id.shipping_id
    WHERE ed.delivered_date IS NOT NULL AND id.received_date IS NOT NULL
    GROUP BY oh.product_id
),
categorized_products AS (
    SELECT 
        product_id,
        avg_shipping_days,
        CASE 
            WHEN avg_shipping_days <= 5 THEN 'Fast (≤5 days)'
            WHEN avg_shipping_days <= 10 THEN 'Normal (6-10 days)'
            WHEN avg_shipping_days <= 15 THEN 'Slow (11-15 days)'
            ELSE 'Very Slow (>15 days)'
        END AS shipping_speed
    FROM product_shipping
)
SELECT
    cp.shipping_speed,
    COUNT(DISTINCT cp.product_id) AS products_count,
    COUNT(cr.review_id) AS total_reviews,
    ROUND(AVG(cr.rating), 2) AS avg_rating,
    COUNT(CASE WHEN cr.rating = 5 THEN 1 END) AS five_star,
    COUNT(CASE WHEN cr.rating = 4 THEN 1 END) AS four_star,
    COUNT(CASE WHEN cr.rating = 3 THEN 1 END) AS three_star,
    COUNT(CASE WHEN cr.rating = 2 THEN 1 END) AS two_star,
    COUNT(CASE WHEN cr.rating = 1 THEN 1 END) AS one_star,
    ROUND(AVG(cp.avg_shipping_days), 1) AS avg_days
FROM categorized_products cp
LEFT JOIN customer_review cr ON cp.product_id = cr.product_id
GROUP BY cp.shipping_speed, 
    CASE 
        WHEN cp.avg_shipping_days <= 5 THEN 1
        WHEN cp.avg_shipping_days <= 10 THEN 2
        WHEN cp.avg_shipping_days <= 15 THEN 3
        ELSE 4
    END
ORDER BY 
    CASE 
        WHEN cp.shipping_speed = 'Fast (≤5 days)' THEN 1
        WHEN cp.shipping_speed = 'Normal (6-10 days)' THEN 2
        WHEN cp.shipping_speed = 'Slow (11-15 days)' THEN 3
        ELSE 4
    END;


-- Staff performance ranking: tickets handled, hours logged, avg time per ticket, customer/seller split.

select 
	s.first_name, s.last_name,
	count(*) as total_ticket,
	round(avg(cs.duration_hours),2) as avg_service_hour
from customer_service as cs 
join staff as s on cs.staff_id = s.staff_id 
group by s.first_name, s.last_name 
having count(*) > 3
order by avg_service_hour desc