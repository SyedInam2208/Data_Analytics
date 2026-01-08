-- PostgreSQL DDL for datasource CSV files
-- Create database schema for customers, products, and purchase data

-- Table: customers
-- Source: datasource/customers.csv
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_type VARCHAR(50) NOT NULL
);

-- Table: products
-- Source: datasource/products.csv
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    item VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

-- Table: invoice_items
-- Source: datasource/invoice_items.csv
-- Note: Contains duplicate (invoice_id, product_id) pairs - needs cleaning
CREATE TABLE invoice_items (
    uid SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    line_total NUMERIC(10, 2) NOT NULL
);

-- Table: purchases
-- Source: datasource/purchases.csv
-- Note: Contains duplicate (invoice_id, product_id) pairs - needs cleaning
CREATE TABLE purchases (
    uid SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    purchase_date DATE NOT NULL,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_product_id ON invoice_items(product_id);
CREATE INDEX idx_purchases_invoice_id ON purchases(invoice_id);
CREATE INDEX idx_purchases_customer_id ON purchases(customer_id);
CREATE INDEX idx_purchases_product_id ON purchases(product_id);
CREATE INDEX idx_purchases_date ON purchases(purchase_date);
CREATE INDEX idx_customers_type ON customers(customer_type);
CREATE INDEX idx_products_category ON products(category);
