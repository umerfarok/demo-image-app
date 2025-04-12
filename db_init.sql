-- Database initialization script

-- Create the database
CREATE DATABASE IF NOT EXISTS product_generator;

-- Use the database
USE product_generator;

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    item_sku VARCHAR(100) NOT NULL,
    parent_child ENUM('Parent', 'Child') NOT NULL,
    parent_sku VARCHAR(100) NULL,
    size VARCHAR(50) NULL,
    color VARCHAR(50) NULL,
    image_url TEXT NULL,
    marketplace_title TEXT NULL,
    category VARCHAR(100) NULL,
    tax_class VARCHAR(50) NULL,
    quantity INT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mockup_id VARCHAR(100) NULL,
    smart_object_uuid VARCHAR(100) NULL,
    
    -- Add indexes for better performance
    INDEX idx_item_sku (item_sku),
    INDEX idx_parent_child (parent_child),
    INDEX idx_parent_sku (parent_sku),
    INDEX idx_category (category)
);

-- Add sample product (optional, uncomment if you want a sample product)
-- INSERT INTO products (product_name, item_sku, parent_child, size, color, quantity, price, category)
-- VALUES ('Sample T-Shirt', 'TS-001', 'Parent', 'M', 'Black', 10, 19.99, 'Apparel > T-shirts');
