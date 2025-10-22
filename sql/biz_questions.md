# Business Requirements for SQL Analysis

## Approach

Work through real-world business questions that demonstrate your ability to translate business needs into SQL solutions. Questions are organized by business domain and complexity level (Basic → Expert).

## Category 1: Revenue & Financial Analysis

**Q1.1** (Basic): What is the total revenue generated from all completed orders?

**Q1.2** (Intermediate): Calculate monthly revenue trends. Show month, total revenue, order count, and average order value.

**Q1.3** (Advanced): Calculate month-over-month revenue growth percentage with running totals.

- *Demonstrates: Window functions (LAG, SUM OVER), CTEs*

**Q1.4** (Advanced): Which product categories generate the most revenue? Include percentage of total revenue and cumulative percentage for Pareto analysis.

- *Demonstrates: Window functions, percentage calculations*

**Q1.5** (Expert): Calculate revenue per seller with 10% platform fee deduction. Rank sellers by net revenue and identify top 20% performers.

- *Demonstrates: Complex calculations, NTILE, CTEs*

## Category 2: Customer Analytics & Behavior

**Q2.1** (Basic): How many customers have made at least one purchase?

**Q2.2** (Intermediate): Calculate customer lifetime value (CLV). Show top 10 customers by total spend.

**Q2.3** (Advanced): Perform RFM analysis (Recency, Frequency, Monetary). Segment customers into: Champions, Loyal, At-Risk, Lost.

- *Demonstrates: CASE statements, date calculations, scoring logic, CTEs*

**Q2.4** (Advanced): Calculate customer retention rate by cohort (group by first purchase month, track repeat purchases).

- *Demonstrates: Self-joins, cohort analysis, window functions*

**Q2.5** (Expert): Find customers who bid but never purchased. Calculate their total bid activity and potential lost revenue.

- *Demonstrates: Complex JOINs, NOT EXISTS patterns, aggregations*

## Category 3: Product & Inventory Insights

**Q3.1** (Basic): List top 10 best-selling products by quantity sold.

**Q3.2** (Intermediate): Which products have the highest average customer rating? (minimum 3 reviews)

**Q3.3** (Advanced): Product performance dashboard - units sold, revenue, average rating, review count, bid activity (total bids, unique bidders).

- *Demonstrates: Multiple JOINs, complex aggregations, subqueries*

**Q3.4** (Advanced): Identify slow-moving inventory (products with less than 2 units sold).

- *Demonstrates: LEFT JOINs, NULL handling*

**Q3.5** (Expert): Calculate bid-to-purchase conversion rate by product.

- *Demonstrates: Complex joins, DISTINCT counting, percentage calculations*

## Category 4: Seller Performance & Operations

**Q4.1** (Basic): How many active sellers have listed at least one product?

**Q4.2** (Intermediate): Seller performance scorecard: products listed, total sales, revenue, average rating.

**Q4.3** (Advanced): Rank top sellers using weighted score: revenue (40%), sales count (30%), avg rating (30%).

- *Demonstrates: Weighted calculations, ranking, normalization*

**Q4.4** (Advanced): Sellers who required support - show seller ID, service requests, support hours, and sales performance.

- *Demonstrates: Multi-table JOINs, aggregations*

**Q4.5** (Expert): Seller churn risk - identify sellers with no sales in last 90 days or declining sales trends.

- *Demonstrates: Temporal analysis, trend detection, window functions*

## Category 5: Bidding & Auction Analysis

**Q5.1** (Intermediate): Average bids per product. Which products have most competitive bidding?

**Q5.2** (Advanced): For products with bids - show starting price, highest bid, bidder count, bid range, sale status.

- *Demonstrates: Multiple aggregations, CASE statements, JOINs*

**Q5.3** (Advanced): Bid timing analysis - patterns by hour of day and day of week.

- *Demonstrates: EXTRACT, DATE_TRUNC, time-series aggregations*

**Q5.4** (Expert): Identify "serial bidders" - high bid frequency but low purchase conversion rate.

- *Demonstrates: CTEs, ratio calculations, behavioral pattern detection*

**Q5.5** (Expert): Price escalation analysis - show bidding progression over time using running maximum.

- *Demonstrates: Window functions (MAX OVER with ORDER BY), temporal sequencing*

## Category 6: Operational Efficiency & Service Quality

**Q6.1** (Intermediate): Average shipping time (days) by carrier.

**Q6.2** (Advanced): Customer service metrics dashboard: total tickets, average resolution time, tickets by customer segment (CLV tier).

- *Demonstrates: CTEs for segmentation, aggregations, multi-level JOINs*

**Q6.3** (Advanced): Orders with shipping delays (not shipped within 3 days). Correlate with customer review scores.

- *Demonstrates: Date arithmetic, correlation analysis*

**Q6.4** (Expert): Staff performance ranking: tickets handled, hours logged, avg time per ticket, customer/seller split.

- *Demonstrates: Window functions (RANK), FILTER clause, complex aggregations*

## Category 7: Data Quality & Business Rules

**Q7.1** (Intermediate): Find data quality issues - orders without payment, products without seller, missing emails.

**Q7.2** (Advanced): Identify business rule violations:

- Bids after order creation
- Payment mismatches
- Duplicate emails
- *Demonstrates: Complex WHERE conditions, data validation*

**Q7.3** (Advanced): Data quality dashboard - % complete records, orphaned records by table, constraint violations.

- *Demonstrates: UNION ALL, percentage calculations, data profiling*

**Q7.4** (Expert): Anomaly detection - unusual bid amounts (3+ standard deviations), high-frequency suspicious orders.

- *Demonstrates: STDDEV, statistical functions, outlier detection*

## Implementation Guidelines

For each question:

1. **Write commented SQL** explaining your logic
2. **Organize by category** in separate files (e.g., `sql/01_revenue_analysis.sql`)
3. **Include sample output** in comments or README
4. **Document business insights** - what decisions can be made?
5. **Show optimization notes** for complex queries (indexes, EXPLAIN plans)
6. **Use multiple approaches** where applicable (compare window functions vs subqueries)

## Suggested Workflow

**Phase 1** (Week 1): Basic & Intermediate questions across all categories

**Phase 2** (Week 2): Advanced questions with CTEs and window functions

**Phase 3** (Week 3): Expert-level queries and optimization

**Phase 4** (Week 4): Stored procedures, triggers, comprehensive README

## File Structure

```
sql/
├── 01_revenue_analysis.sql (Q1.1-Q1.5)
├── 02_customer_analytics.sql (Q2.1-Q2.5)
├── 03_product_insights.sql (Q3.1-Q3.5)
├── 04_seller_performance.sql (Q4.1-Q4.5)
├── 05_bidding_analysis.sql (Q5.1-Q5.5)
├── 06_operational_metrics.sql (Q6.1-Q6.4)
├── 07_data_quality.sql (Q7.1-Q7.4)
├── 08_stored_procedures.sql (optional - business logic layer)
└── 09_triggers.sql (optional - automation & integrity)
```

## Skills Showcased

- Business requirement translation
- Advanced SQL (CTEs, window functions, recursive queries)
- Statistical analysis and anomaly detection
- Performance optimization awareness
- Data quality and validation
- Real-world problem solving