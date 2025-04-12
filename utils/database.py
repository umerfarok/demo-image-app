import mysql.connector
from mysql.connector import Error
import streamlit as st
import pandas as pd
from config import DB_CONFIG

class Database:
    def __init__(self):
        """Initialize database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                
                # Create tables if they don't exist
                self._create_tables()
        except Error as e:
            st.error(f"Database connection error: {e}")
            self.connection = None
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        create_products_table = """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            item_sku VARCHAR(100) NOT NULL,
            parent_child ENUM('Parent', 'Child') NOT NULL,
            parent_sku VARCHAR(100) NULL,
            size TEXT NULL,
            color TEXT NULL,
            image_url TEXT NULL,
            marketplace_title TEXT NULL,
            category VARCHAR(100) NULL,
            tax_class VARCHAR(50) NULL,
            quantity INT NOT NULL DEFAULT 0,
            price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mockup_id VARCHAR(100) NULL,
            smart_object_uuid VARCHAR(100) NULL
        )
        """
        self.cursor.execute(create_products_table)
        self.connection.commit()
        
        # Alter table to modify columns if they already exist with smaller size
        try:
            alter_size_query = "ALTER TABLE products MODIFY COLUMN size TEXT"
            self.cursor.execute(alter_size_query)
            
            alter_color_query = "ALTER TABLE products MODIFY COLUMN color TEXT"
            self.cursor.execute(alter_color_query)
            
            # Add mockup_id and smart_object_uuid columns if they don't exist
            check_column_query = """
            SELECT COUNT(*) as column_exists FROM information_schema.columns 
            WHERE table_schema = DATABASE() AND table_name = 'products' AND column_name = 'mockup_id'
            """
            self.cursor.execute(check_column_query)
            result = self.cursor.fetchone()
            
            if result and result['column_exists'] == 0:
                add_column_query = """
                ALTER TABLE products 
                ADD COLUMN mockup_id VARCHAR(100) NULL,
                ADD COLUMN smart_object_uuid VARCHAR(100) NULL
                """
                self.cursor.execute(add_column_query)
                
            self.connection.commit()
        except Error as e:
            st.warning(f"Table alteration notice: {e}")
    
    def add_product(self, product_data):
        """
        Add a new product to the database
        
        Args:
            product_data (dict): Product data dictionary
            
        Returns:
            int: Product ID if inserted successfully, None otherwise
        """
        try:
            query = """
            INSERT INTO products (
                product_name, item_sku, parent_child, parent_sku, size, color, 
                image_url, marketplace_title, category, tax_class, quantity, price,
                mockup_id, smart_object_uuid
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                product_data['product_name'],
                product_data['item_sku'],
                product_data['parent_child'],
                product_data['parent_sku'],
                product_data['size'],
                product_data['color'],
                product_data['image_url'],
                product_data['marketplace_title'],
                product_data['category'],
                product_data['tax_class'],
                product_data['quantity'],
                product_data['price'],
                product_data['mockup_id'],
                product_data['smart_object_uuid'],
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            st.error(f"Error adding product: {e}")
            return None
    
    def get_all_products(self):
        """
        Get all products from database
        
        Returns:
            DataFrame: Products as pandas DataFrame or None if error
        """
        try:
            query = "SELECT * FROM products ORDER BY created_at DESC"
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            df = pd.DataFrame(result) if result else pd.DataFrame()
            
            # Ensure image_url is properly formatted if using S3
            # This ensures any relative paths are converted to absolute when needed
            # but preserves S3 URLs as they are
            if not df.empty and 'image_url' in df.columns:
                from utils.api import is_s3_url
                import os
                
                def format_image_url(url):
                    if not url:
                        return url
                    if is_s3_url(url):
                        return url  # S3 URLs are already complete
                    # Convert relative paths to absolute if needed
                    elif os.path.exists(url):
                        return os.path.abspath(url)
                    return url
                
                df['image_url'] = df['image_url'].apply(format_image_url)
            
            return df
        except Error as e:
            st.error(f"Error retrieving products: {e}")
            return pd.DataFrame()
    
    def get_product(self, product_id):
        """
        Get a specific product by ID
        
        Args:
            product_id (int): Product ID
            
        Returns:
            dict: Product data or None if not found
        """
        try:
            query = "SELECT * FROM products WHERE id = %s"
            self.cursor.execute(query, (product_id,))
            return self.cursor.fetchone()
        except Error as e:
            st.error(f"Error retrieving product {product_id}: {e}")
            return None
    
    def update_product(self, product_id, product_data):
        """
        Update a product
        
        Args:
            product_id (int): Product ID to update
            product_data (dict): Updated product data
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            query = """
            UPDATE products SET
                product_name = %s,
                item_sku = %s,
                parent_child = %s,
                parent_sku = %s,
                size = %s,
                color = %s,
                image_url = %s,
                marketplace_title = %s,
                category = %s,
                tax_class = %s,
                quantity = %s,
                price = %s
            WHERE id = %s
            """
            values = (
                product_data['product_name'],
                product_data['item_sku'],
                product_data['parent_child'],
                product_data['parent_sku'],
                product_data['size'],
                product_data['color'],
                product_data['image_url'],
                product_data['marketplace_title'],
                product_data['category'],
                product_data['tax_class'],
                product_data['quantity'],
                product_data['price'],
                product_id
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            st.error(f"Error updating product {product_id}: {e}")
            return False
    
    def delete_product(self, product_id):
        """
        Delete a product
        
        Args:
            product_id (int): Product ID to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            query = "DELETE FROM products WHERE id = %s"
            self.cursor.execute(query, (product_id,))
            self.connection.commit()
            return True
        except Error as e:
            st.error(f"Error deleting product {product_id}: {e}")
            return False
    
    def get_stats(self):
        """
        Get basic statistics for dashboard
        
        Returns:
            dict: Dictionary containing stats
        """
        try:
            # Total products
            self.cursor.execute("SELECT COUNT(*) as total FROM products")
            total_products = self.cursor.fetchone()['total']
            
            # Total parent products
            self.cursor.execute("SELECT COUNT(*) as parent_count FROM products WHERE parent_child = 'Parent'")
            parent_count = self.cursor.fetchone()['parent_count']
            
            # Total images stored
            self.cursor.execute("SELECT COUNT(*) as image_count FROM products WHERE image_url IS NOT NULL")
            image_count = self.cursor.fetchone()['image_count']
            
            return {
                'total_products': total_products,
                'parent_count': parent_count,
                'image_count': image_count
            }
        except Error as e:
            st.error(f"Error getting stats: {e}")
            return {
                'total_products': 0,
                'parent_count': 0,
                'image_count': 0
            }
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'connection') and self.connection is not None and self.connection.is_connected():
            if hasattr(self, 'cursor'):
                self.cursor.close()
            self.connection.close()

# Create connection pool
@st.cache_resource
def get_database_connection():
    """
    Get a cached database connection
    
    Returns:
        Database: Database connection instance
    """
    return Database()
