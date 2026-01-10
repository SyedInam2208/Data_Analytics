-- Recreate schema every run (matches your overwrite load requirement)

DROP TABLE IF EXISTS invoice_items;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_type TEXT
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    item TEXT,
    category TEXT,
    price NUMERIC
);

-- Invoice header table (derived from purchases.csv)
CREATE TABLE purchases (
    invoice_id TEXT PRIMARY KEY,
    purchase_date TIMESTAMP,
    customer_id TEXT NOT NULL,
    CONSTRAINT fk_purchases_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Line item table
CREATE TABLE invoice_items (
    invoice_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity NUMERIC,
    unit_price NUMERIC,
    line_total NUMERIC,
    CONSTRAINT fk_items_invoice
        FOREIGN KEY (invoice_id) REFERENCES purchases(invoice_id),
    CONSTRAINT fk_items_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Helpful indexes
CREATE INDEX idx_purchases_customer_id ON purchases(customer_id);
CREATE INDEX idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_product_id ON invoice_items(product_id);
CREATE INDEX idx_products_category ON products(category);
