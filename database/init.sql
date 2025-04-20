CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    in_stock BOOLEAN DEFAULT true
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL
);

-- Insert sample bakery products
INSERT INTO products (name, description, price, in_stock) VALUES
('Chocolate Cake', 'Rich chocolate cake with chocolate frosting', 25.99, true),
('Sourdough Bread', 'Artisanal sourdough bread', 6.50, true),
('Blueberry Muffin', 'Muffin filled with fresh blueberries', 3.99, true),
('Croissant', 'Buttery, flaky croissant', 2.99, true),
('Apple Pie', 'Traditional apple pie with cinnamon', 18.99, true),
('Cinnamon Roll', 'Soft roll with cinnamon and cream cheese frosting', 4.50, true);