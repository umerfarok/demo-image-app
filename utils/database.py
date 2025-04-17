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
        
        # Create generated_products table if it doesn't exist
        create_generated_products_table = """
        CREATE TABLE IF NOT EXISTS generated_products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            item_sku VARCHAR(100) NULL,
            marketplace_title TEXT NULL,
            size TEXT NULL,
            color TEXT NULL,
            original_design_url TEXT NULL,
            mockup_urls TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_published BOOLEAN DEFAULT FALSE,
            parent_product_id INT NULL,
            parent_sku VARCHAR(100) NULL,
            parent_child VARCHAR(10) DEFAULT 'Child',

            INDEX idx_item_sku (item_sku),
            INDEX idx_parent_sku (parent_sku),
            INDEX idx_created_at (created_at),
            INDEX idx_is_published (is_published),
            INDEX idx_parent_product_id (parent_product_id)
        )
        """
        self.cursor.execute(create_generated_products_table)
        
        # Check if columns exist and add them if they don't
        try:
            # Check if mockup_id column exists
            self.cursor.execute("SHOW COLUMNS FROM products LIKE 'mockup_id'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE products ADD COLUMN mockup_id VARCHAR(255) NULL")
            
            # Check if smart_object_uuid column exists
            self.cursor.execute("SHOW COLUMNS FROM products LIKE 'smart_object_uuid'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE products ADD COLUMN smart_object_uuid VARCHAR(255) NULL")
            
            # Check if item_sku column exists in generated_products
            self.cursor.execute("SHOW COLUMNS FROM generated_products LIKE 'item_sku'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE generated_products ADD COLUMN item_sku VARCHAR(100) NULL")
                self.cursor.execute("ALTER TABLE generated_products ADD INDEX idx_item_sku (item_sku)")
            
            # Check if parent_sku column exists in generated_products
            self.cursor.execute("SHOW COLUMNS FROM generated_products LIKE 'parent_sku'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE generated_products ADD COLUMN parent_sku VARCHAR(100) NULL")
                
            self.connection.commit()
        except Error as e:
            st.error(f"Error modifying tables: {e}")
        
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
            
    def create_generated_product(self, product_data):
        """
        Add a new generated product to the database
        
        Args:
            product_data (dict): Generated product data containing:
                - product_name: Name of the product
                - item_sku: Unique SKU for the design (was design_sku)
                - marketplace_title: Title for marketplace listings
                - size: JSON string of available sizes
                - color: JSON string of available colors (hex values)
                - original_design_url: URL to the original design in S3
                - mockup_urls: JSON string mapping color hex codes to S3 mockup URLs
                - parent_product_id: Optional reference to a parent product
            
        Returns:
            int: Product ID if inserted successfully, None otherwise
        """
        try:
            # Check if the table exists, create it if not
            self._ensure_generated_products_table()
            
            # Validate required fields
            if 'product_name' not in product_data:
                st.error("Missing required field: product_name")
                return None
                
            # Handle case where design_sku is provided instead of item_sku
            if 'item_sku' not in product_data and 'design_sku' in product_data:
                product_data['item_sku'] = product_data['design_sku']
                st.info(f"Using design_sku as item_sku: {product_data['item_sku']}")
            
            if 'item_sku' not in product_data:
                st.error("Missing required field: item_sku")
                return None
            
            # Check if SKU already exists to avoid duplicates
            query = "SELECT COUNT(*) as count FROM generated_products WHERE item_sku = %s"
            self.cursor.execute(query, (product_data['item_sku'],))
            result = self.cursor.fetchone()
            if result and result['count'] > 0:
                st.warning(f"SKU {product_data['item_sku']} already exists in database. Using it anyway.")
            
            # Set parent_sku based on parent_product_id if available
            parent_sku = product_data.get('parent_sku', '')
            if not parent_sku and 'parent_product_id' in product_data and product_data['parent_product_id']:
                # Fetch parent product's SKU
                parent_query = "SELECT item_sku FROM products WHERE id = %s"
                self.cursor.execute(parent_query, (product_data['parent_product_id'],))
                parent_result = self.cursor.fetchone()
                if parent_result:
                    parent_sku = parent_result['item_sku']
                
            query = """
            INSERT INTO generated_products (
                product_name, parent_sku, marketplace_title, size, color,
                original_design_url, mockup_urls, is_published, parent_product_id, item_sku
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Default to not published
            is_published = product_data.get('is_published', False)
            
            values = (
                product_data['product_name'],
                parent_sku,  # Use the determined parent_sku
                product_data.get('marketplace_title', ''),
                product_data.get('size', '[]'),
                product_data.get('color', '[]'),
                product_data.get('original_design_url', ''),
                product_data.get('mockup_urls', '{}'),
                is_published,
                product_data.get('parent_product_id', None),
                product_data['item_sku']  # Make sure item_sku is included
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            new_id = self.cursor.lastrowid
            st.success(f"Generated product '{product_data['product_name']}' added with ID: {new_id}")
            return new_id
        except KeyError as e:
            st.error(f"Error adding generated product - missing required field: {e}")
            return None
        except Error as e:
            st.error(f"Error adding generated product: {e}")
            return None
    
    def update_generated_product(self, product_id, product_data):
        """
        Update a generated product
        
        Args:
            product_id (int): Generated Product ID to update
            product_data (dict): Updated product data
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            query = """
            UPDATE generated_products SET
                product_name = %s,
                item_sku = %s,
                parent_sku = %s,
                marketplace_title = %s,
                size = %s,
                color = %s,
                original_design_url = %s,
                mockup_urls = %s,
                is_published = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            # Default to current published state if not specified
            is_published = product_data.get('is_published', False)
            
            values = (
                product_data['product_name'],
                product_data.get('item_sku', ''),
                product_data.get('parent_sku', ''),
                product_data.get('marketplace_title', ''),
                product_data.get('size', '[]'),
                product_data.get('color', '[]'),
                product_data.get('original_design_url', ''),
                product_data.get('mockup_urls', '{}'),
                is_published,
                product_id
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Error as e:
            st.error(f"Error updating generated product {product_id}: {e}")
            return False
    
    def get_all_generated_products(self):
        """
        Get all generated products from database
        
        Returns:
            DataFrame: Generated products as pandas DataFrame or None if error
        """
        try:
            # Ensure the table exists
            self._ensure_generated_products_table()
            
            query = "SELECT * FROM generated_products ORDER BY created_at DESC"
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return pd.DataFrame(result) if result else pd.DataFrame()
        except Error as e:
            st.error(f"Error retrieving generated products: {e}")
            return pd.DataFrame()
    
    def get_generated_product(self, product_id):
        """
        Get a specific generated product by ID
        
        Args:
            product_id (int): Generated Product ID
            
        Returns:
            dict: Product data or None if not found
        """
        try:
            query = "SELECT * FROM generated_products WHERE id = %s"
            self.cursor.execute(query, (product_id,))
            return self.cursor.fetchone()
        except Error as e:
            st.error(f"Error retrieving generated product {product_id}: {e}")
            return None
            
    def _ensure_generated_products_table(self):
        """Create the generated_products table if it doesn't exist"""
        try:
            # This is now handled in _create_tables() during initialization
            # Keep this method for backward compatibility with existing code
            pass
        except Error as e:
            st.warning(f"Table creation notice: {e}")

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

    def delete_generated_product(self, product_id):
        """
        Delete a generated product
        
        Args:
            product_id (int): Generated Product ID to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            query = "DELETE FROM generated_products WHERE id = %s"
            self.cursor.execute(query, (product_id,))
            self.connection.commit()
            return True
        except Error as e:
            st.error(f"Error deleting generated product {product_id}: {e}")
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
    
    def check_if_sku_exists(self, sku):
        """
        Check if a SKU already exists in the database
        
        Args:
            sku (str): The SKU to check
            
        Returns:
            bool: True if the SKU exists, False otherwise
        """
        try:
            # Use the existing cursor
            cursor = self.cursor if hasattr(self, 'cursor') else self.connection.cursor()
            
            # Execute query to check if SKU exists in generated_products table
            cursor.execute(
                "SELECT COUNT(*) as count FROM generated_products WHERE item_sku = %s OR parent_sku = %s", 
                (sku, sku)
            )
            
            # Get the result
            result = cursor.fetchone()
            count = result['count'] if isinstance(result, dict) else result[0]
            
            return count > 0
        except Exception as e:
            st.error(f"Error checking if SKU exists: {e}")
            return False
    
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
