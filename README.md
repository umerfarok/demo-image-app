# Product Generator App

A Streamlit application for generating product mockups using DynamicMockups API, storing images in AWS S3, and managing product data with CSV export capabilities.

## Features

- Generate product mockups using DynamicMockups API
- Store images in AWS S3 for scalable cloud storage
- Manage product metadata in a MySQL database
- Export product data to a specific CSV format
- Basic authentication system

## Prerequisites

- Python 3.7+
- MySQL database
- AWS account with S3 access
- DynamicMockups API key

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd dynamic-image-genapp
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your database credentials, API key, and AWS S3 credentials.

4. Set up the MySQL database:
   ```sql
   CREATE DATABASE product_generator;
   
   USE product_generator;
   
   CREATE TABLE products (
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
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

5. Create an S3 bucket:
   - Log in to your AWS console
   - Create a new S3 bucket
   - Set the appropriate permissions for public read access
   - Create folders named `original` and `mockups` in the bucket

## Usage

1. Start the application:
   ```
   streamlit run app.py
   ```

2. Log in using the default credentials:
   - Email: admin@example.com
   - Password: password123

3. Use the sidebar to navigate between pages:
   - Home: Dashboard with statistics and quick links
   - Add Product: Create new products and generate mockups
   - Product List: View and manage existing products
   - Export: Export product data to CSV

## Deployment

The application can be deployed using Docker:

```bash
docker build -t product-generator-app .
docker run -p 8501:8501 product-generator-app
```

For deployment on Railway.app or Render.com, connect your GitHub repository and use the provided Dockerfile.

## CSV Export Format

The exported CSV follows this format:
- Product Name
- Item SKU
- Parent/Child
- Parent SKU
- Size
- Colour
- Image URL (S3 URLs for images)
- Marketplace Title
- Woocommerce Product Category
- Tax Class
- Qty
- Price

## S3 Storage Benefits

Using AWS S3 for image storage provides:
1. Scalability - Store thousands of images
2. Reliability - 99.999999999% durability
3. Cost-effectiveness - Pay only for what you use
4. Performance - Fast global access with CDN capability
5. Security - Configurable access controls

## Default Login

- Email: admin@example.com
- Password: password123

*Note: In a production environment, you should change these credentials.*
