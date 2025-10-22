-- =============================================
-- eBay-like Marketplace Database Schema
-- Database: PostgreSQL
-- Purpose: Data Engineering Portfolio Project
-- =============================================

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS export_distribution CASCADE;
DROP TABLE IF EXISTS import_distribution CASCADE;
DROP TABLE IF EXISTS seller_review CASCADE;
DROP TABLE IF EXISTS customer_review CASCADE;
DROP TABLE IF EXISTS seller_service CASCADE;
DROP TABLE IF EXISTS customer_service CASCADE;
DROP TABLE IF EXISTS order_history CASCADE;
DROP TABLE IF EXISTS payment CASCADE;
DROP TABLE IF EXISTS shipping CASCADE;
DROP TABLE IF EXISTS order_header CASCADE;
DROP TABLE IF EXISTS bid CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS app_user CASCADE;
DROP TABLE IF EXISTS customer CASCADE;
DROP TABLE IF EXISTS seller CASCADE;
DROP TABLE IF EXISTS staff CASCADE;
DROP TABLE IF EXISTS department CASCADE;

-- =============================================
-- CORE ENTITY TABLES
-- =============================================

-- Department: Organization departments (Electronics, Fashion, etc.)
CREATE TABLE department (
    depart_id INTEGER PRIMARY KEY,
    depart_name VARCHAR(50) NOT NULL
);

-- Staff: Employees who manage departments and provide services
CREATE TABLE staff (
    staff_id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL,
    last_name VARCHAR(20) NOT NULL,
    first_name VARCHAR(20) NOT NULL,
    CONSTRAINT fk_staff_department FOREIGN KEY (department_id) 
        REFERENCES department(depart_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- Seller: Vendors who list products on the marketplace
CREATE TABLE seller (
    seller_id INTEGER PRIMARY KEY,
    description VARCHAR(200),
    address VARCHAR(100),
    state_province VARCHAR(2)
);

-- Customer: Buyers who purchase products
CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(20) NOT NULL,
    last_name VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    address VARCHAR(100),
    state VARCHAR(2)
);

-- App_User: Application users (both customers and sellers)
CREATE TABLE app_user (
    user_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    seller_id INTEGER,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(50) NOT NULL,
    registed_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_appuser_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_appuser_seller FOREIGN KEY (seller_id) 
        REFERENCES seller(seller_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT chk_user_type CHECK (
        (customer_id IS NOT NULL AND seller_id IS NULL) OR
        (customer_id IS NULL AND seller_id IS NOT NULL)
    )
);

-- =============================================
-- PRODUCT & BIDDING TABLES
-- =============================================

-- Product: Items listed for sale
CREATE TABLE product (
    product_id INTEGER PRIMARY KEY,
    seller_id INTEGER NOT NULL,
    description VARCHAR(200),
    category VARCHAR(20),
    product_price DECIMAL(10,2) NOT NULL CHECK (product_price >= 0),
    product_name VARCHAR(50) NOT NULL,
    CONSTRAINT fk_product_seller FOREIGN KEY (seller_id) 
        REFERENCES seller(seller_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Bid: Customer bids on products
CREATE TABLE bid (
    bid_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    bid_amount DECIMAL(10,2) NOT NULL CHECK (bid_amount > 0),
    bid_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_bid_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_bid_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================
-- ORDER & FULFILLMENT TABLES
-- =============================================

-- Shipping: Shipping information for orders
CREATE TABLE shipping (
    shipping_id INTEGER PRIMARY KEY,
    carrier VARCHAR(50),
    shipping_date TIMESTAMP
);

-- Order_Header: Main order records
CREATE TABLE order_header (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    bid_id INTEGER,
    product_id INTEGER NOT NULL,
    shipping_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    order_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_order_bid FOREIGN KEY (bid_id) 
        REFERENCES bid(bid_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_order_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_order_shipping FOREIGN KEY (shipping_id) 
        REFERENCES shipping(shipping_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- Payment: Payment records for orders
CREATE TABLE payment (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) 
        REFERENCES order_header(order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Order_History: Historical record of customer orders
CREATE TABLE order_history (
    history_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    CONSTRAINT fk_history_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_history_order FOREIGN KEY (order_id) 
        REFERENCES order_header(order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================
-- LOGISTICS TABLES
-- =============================================

-- Import_Distribution: Tracking incoming international shipments
CREATE TABLE import_distribution (
    import_id INTEGER PRIMARY KEY,
    shipping_id INTEGER NOT NULL,
    received_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_import_shipping FOREIGN KEY (shipping_id) 
        REFERENCES shipping(shipping_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Export_Distribution: Tracking outgoing international shipments
CREATE TABLE export_distribution (
    export_id INTEGER PRIMARY KEY,
    shipping_id INTEGER NOT NULL,
    delivered_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_export_shipping FOREIGN KEY (shipping_id) 
        REFERENCES shipping(shipping_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================
-- SERVICE & REVIEW TABLES
-- =============================================

-- Customer_Service: Support tickets for customers
CREATE TABLE customer_service (
    cservice_id INTEGER PRIMARY KEY,
    staff_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    duration_hours NUMERIC(4,1) NOT NULL CHECK (duration_hours > 0),
    service_date DATE NOT NULL,
    description VARCHAR(200),
    CONSTRAINT fk_cservice_staff FOREIGN KEY (staff_id) 
        REFERENCES staff(staff_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_cservice_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Seller_Service: Support and consultation for sellers
CREATE TABLE seller_service (
    sservice_id INTEGER PRIMARY KEY,
    seller_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    duration_hours NUMERIC(4,1) NOT NULL CHECK (duration_hours > 0),
    service_date DATE NOT NULL,
    description VARCHAR(500),
    CONSTRAINT fk_sservice_seller FOREIGN KEY (seller_id) 
        REFERENCES seller(seller_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_sservice_staff FOREIGN KEY (staff_id) 
        REFERENCES staff(staff_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- Customer_Review: Product reviews from customers
CREATE TABLE customer_review (
    review_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    description VARCHAR(200),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_creview_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_creview_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Seller_Review: Seller performance reviews
CREATE TABLE seller_review (
    sreview_id INTEGER PRIMARY KEY,
    seller_id INTEGER NOT NULL,
    description VARCHAR(200),
    CONSTRAINT fk_sreview_seller FOREIGN KEY (seller_id) 
        REFERENCES seller(seller_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================
-- INDEXES for Performance Optimization
-- =============================================

-- Indexes on foreign keys for JOIN performance
CREATE INDEX idx_staff_department ON staff(department_id);
CREATE INDEX idx_appuser_customer ON app_user(customer_id);
CREATE INDEX idx_appuser_seller ON app_user(seller_id);
CREATE INDEX idx_product_seller ON product(seller_id);
CREATE INDEX idx_product_category ON product(category);
CREATE INDEX idx_bid_product ON bid(product_id);
CREATE INDEX idx_bid_customer ON bid(customer_id);
CREATE INDEX idx_bid_date ON bid(bid_date);
CREATE INDEX idx_order_customer ON order_header(customer_id);
CREATE INDEX idx_order_product ON order_header(product_id);
CREATE INDEX idx_order_date ON order_header(order_date);
CREATE INDEX idx_payment_order ON payment(order_id);
CREATE INDEX idx_history_customer ON order_history(customer_id);
CREATE INDEX idx_history_order ON order_history(order_id);
CREATE INDEX idx_import_shipping ON import_distribution(shipping_id);
CREATE INDEX idx_export_shipping ON export_distribution(shipping_id);
CREATE INDEX idx_cservice_customer ON customer_service(customer_id);
CREATE INDEX idx_cservice_staff ON customer_service(staff_id);
CREATE INDEX idx_sservice_seller ON seller_service(seller_id);
CREATE INDEX idx_sservice_staff ON seller_service(staff_id);
CREATE INDEX idx_creview_product ON customer_review(product_id);
CREATE INDEX idx_creview_customer ON customer_review(customer_id);
CREATE INDEX idx_sreview_seller ON seller_review(seller_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_bid_product_amount ON bid(product_id, bid_amount DESC);
CREATE INDEX idx_order_customer_date ON order_header(customer_id, order_date DESC);
CREATE INDEX idx_product_seller_category ON product(seller_id, category);

-- =============================================
-- COMMENTS for Documentation
-- =============================================

COMMENT ON TABLE department IS 'Organizational departments managing different product categories';
COMMENT ON TABLE staff IS 'Employees providing customer and seller support services';
COMMENT ON TABLE seller IS 'Vendors listing products on the marketplace';
COMMENT ON TABLE customer IS 'Buyers purchasing products from sellers';
COMMENT ON TABLE app_user IS 'Application users - either customers or sellers';
COMMENT ON TABLE product IS 'Items available for purchase via auction or buy-it-now';
COMMENT ON TABLE bid IS 'Auction bids placed by customers on products';
COMMENT ON TABLE order_header IS 'Completed purchase orders from customers';
COMMENT ON TABLE shipping IS 'Shipping information for order fulfillment';
COMMENT ON TABLE payment IS 'Payment transactions for completed orders';
COMMENT ON TABLE order_history IS 'Historical tracking of customer purchase activity';
COMMENT ON TABLE import_distribution IS 'International incoming shipment tracking';
COMMENT ON TABLE export_distribution IS 'International outgoing shipment tracking';
COMMENT ON TABLE customer_service IS 'Customer support tickets and resolutions';
COMMENT ON TABLE seller_service IS 'Seller support and consultation services';
COMMENT ON TABLE customer_review IS 'Product reviews and ratings from buyers';
COMMENT ON TABLE seller_review IS 'Seller performance feedback';

-- =============================================
-- DATA LOADING HELPER VIEWS (Optional)
-- =============================================

-- View to verify foreign key relationships
CREATE OR REPLACE VIEW vw_data_quality_check AS
SELECT 
    'orphaned_products' AS check_name,
    COUNT(*) AS issue_count
FROM product p
LEFT JOIN seller s ON p.seller_id = s.seller_id
WHERE s.seller_id IS NULL
UNION ALL
SELECT 
    'orphaned_bids',
    COUNT(*)
FROM bid b
LEFT JOIN product p ON b.product_id = p.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT 
    'orphaned_orders',
    COUNT(*)
FROM order_header o
LEFT JOIN customer c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- =============================================
-- END OF DDL SCRIPT
-- =============================================