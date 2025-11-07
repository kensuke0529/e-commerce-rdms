# Data Engineering & SQL Analytics

This directory contains the complete data engineering implementation for the E-Commerce Marketplace platform, including database schema, analytical queries, and data quality validation.

Business Report: [SQL Analysis Report](../result/report.md)

## Database Architecture

### Entity Relationship Diagram

![ERD Diagram](../result/image/conceptual%20diagram%20-%20Physical%20Model.png)

**17-Table Normalized Schema** designed for an eBay-like marketplace:

#### Core Entity Tables

- **department** - Organization departments (Electronics, Fashion, etc.)
- **staff** - Employees managing departments and providing services
- **seller** - Vendors listing products on the marketplace
- **customer** - Buyers purchasing products
- **app_user** - Application users for authentication and access control
- **product** - Product catalog with pricing and seller relationships

#### Transaction Tables

- **order_header** - Order records with customer and product relationships
- **payment** - Payment transactions linked to orders
- **bid** - Bidding activity for auction-style listings
- **shipping** - Shipping and logistics tracking

#### Analytics & Review Tables

- **customer_review** - Customer product reviews and ratings
- **seller_review** - Seller performance reviews
- **order_history** - Historical order tracking

#### Logistics Tables

- **import_distribution** - Incoming international shipment tracking
- **export_distribution** - Outgoing international shipment tracking

#### Service Tables

- **customer_service** - Customer support tickets and resolution tracking
- **seller_service** - Seller support and consultation records

## Analytics & Reporting

### 1. Revenue Analysis

**Business Function**: Comprehensive financial performance tracking and revenue insights

**Key Metrics**:

- Total revenue calculations across all completed orders
- Monthly revenue trends with order count and average order value
- Month-over-month revenue growth percentage with running totals
- Category revenue analysis with Pareto distribution
- Seller revenue rankings with platform fee calculations (10% commission)
- Top 20% seller performance identification

**Business Value**:

- Enables data-driven revenue forecasting
- Identifies high-performing categories and sellers
- Supports commission and fee calculations
- Highlights growth trends and opportunities

### 2. Customer Analytics

**Business Function**: Customer behavior analysis and segmentation for targeted marketing

**Key Metrics**:

- Customer acquisition metrics (customers with purchases)
- Customer Lifetime Value (CLV) calculations
- RFM Analysis (Recency, Frequency, Monetary) segmentation:
  - **Champions**: High value, frequent, recent customers
  - **Loyal**: Regular customers with good value
  - **At-Risk**: Declining engagement customers
  - **Lost**: Inactive customers
- Cohort retention analysis by first purchase month
- Bid-to-purchase conversion tracking
- Lost revenue analysis from non-converting bidders

**Business Value**:

- Enables personalized marketing campaigns
- Identifies high-value customers for retention efforts
- Tracks customer lifecycle and engagement patterns
- Measures conversion funnel effectiveness

### 3. Product Analysis

**Business Function**: Product performance tracking and inventory optimization

**Key Metrics**:

- Best-selling products by quantity and revenue
- Product rating analysis (average ratings with minimum review thresholds)
- Comprehensive product performance dashboard:
  - Units sold
  - Revenue generated
  - Average customer ratings
  - Review counts
  - Bidding activity (total bids, unique bidders)
- Slow-moving inventory identification
- Product-seller performance correlation

**Business Value**:

- Optimizes inventory management
- Identifies top-performing products for promotion
- Highlights products needing attention
- Supports pricing and marketing decisions

### 4. Operational Analysis

**Business Function**: Operational efficiency monitoring and service quality tracking

**Key Metrics**:

- Shipping performance by carrier (average delivery times)
- Customer service metrics dashboard:
  - Total support tickets
  - Average resolution time
  - Tickets segmented by customer CLV tiers
- Shipping delay analysis (orders not shipped within 3 days)
- Delay correlation with customer review scores
- Staff performance rankings:
  - Tickets handled per staff member
  - Hours logged
  - Average time per ticket
  - Customer vs. seller service split

**Business Value**:

- Improves operational efficiency
- Identifies service quality issues
- Enables staff performance benchmarking
- Supports carrier selection decisions

### 5. Data Quality

**Business Function**: Automated data quality monitoring and validation

**Key Checks**:

- Missing email validation in user accounts
- Orders without payment verification
- Products without seller relationships
- Duplicate email detection
- Price validation (payment amount vs. quantity × product_price)
- Business rule violation detection

**Business Value**:

- Ensures data integrity and reliability
- Prevents business logic errors
- Supports compliance and auditing
- Maintains data quality standards

## SQL Analysis Reports

This directory contains SQL query implementations that generate comprehensive analytical reports on the marketplace data. All analysis is performed using SQL queries executed against the PostgreSQL database.

### Analysis Results

Executed query results and analysis are compiled in the [SQL Analysis Report](../result/report.md), which includes:

- Query results with data tables
- Business insights and interpretations
- Key findings and recommendations
- Performance metrics and trends



## Data Validation

The `validation/` directory contains automated SQL queries for data quality monitoring:

### Validation Checks

1. **`missing_email.sql`** - Identifies users with missing email addresses
2. **`orders_without_payment.sql`** - Finds orders that lack payment records
3. **`price_val.sql`** - Validates payment amounts match calculated totals
4. **`product_without_seller.sql`** - Detects products without valid seller relationships

### Validation Process

These validation queries are automatically executed by the data validation system. Results are exported to `result/data_validation_report.txt` with pass/fail metrics.

## Additional Resources

- [Main Project README](../README.md) - Overview of the entire platform
- [Database Schema Documentation](0.tables.sql) - Complete table definitions
- [Business Questions](biz_questions.md) - Detailed business requirements
