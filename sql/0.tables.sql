-- =============================================
-- eBay-like Marketplace Database Schema
-- Database: PostgreSQL
-- Purpose: Data Engineering Portfolio Project
-- =============================================

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

