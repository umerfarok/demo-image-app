import pandas as pd
from config import USE_S3_STORAGE
from utils.api import is_s3_url

def format_products_for_export(df):
    """
    Format products DataFrame for export to CSV
    
    Args:
        df (DataFrame): Products DataFrame
        
    Returns:
        DataFrame: Formatted DataFrame for export
    """
    # Create a copy to avoid modifying the original
    export_df = df.copy()
    
    # Remove database-specific columns
    if 'id' in export_df.columns:
        export_df = export_df.drop(columns=['id'])
    
    if 'created_at' in export_df.columns:
        export_df = export_df.drop(columns=['created_at'])
    
    # Ensure image URLs are properly formatted for export
    if 'image_url' in export_df.columns:
        # Make sure all image URLs are properly formatted
        # For S3 URLs, they should already be complete URLs
        # For local paths, we'll keep them as is
        # This ensures consistent behavior whether S3 is enabled or not
        def format_image_url(url):
            if url and not is_s3_url(url):
                # For local files, we could convert to absolute path
                # but will leave as is since CSV might be used on different systems
                return url
            return url
            
        export_df['image_url'] = export_df['image_url'].apply(format_image_url)
    
    # Rename columns to match required export format
    column_mapping = {
        'product_name': 'Product Name',
        'item_sku': 'Item SKU',
        'parent_child': 'Parent/Child',
        'parent_sku': 'Parent SKU',
        'size': 'Size',
        'color': 'Colour',
        'image_url': 'Image URL',
        'marketplace_title': 'Marketplace Title',
        'category': 'Woocommerce Product Category',
        'tax_class': 'Tax Class',
        'quantity': 'Qty',
        'price': 'Price'
    }
    
    export_df = export_df.rename(columns=column_mapping)
    
    # Ensure columns are in the correct order
    ordered_columns = [
        'Product Name', 'Item SKU', 'Parent/Child', 'Parent SKU',
        'Size', 'Colour', 'Image URL', 'Marketplace Title',
        'Woocommerce Product Category', 'Tax Class', 'Qty', 'Price'
    ]
    
    # Only include columns that exist in the DataFrame
    valid_columns = [col for col in ordered_columns if col in export_df.columns]
    export_df = export_df[valid_columns]
    
    return export_df

def export_to_csv(df):
    """
    Export DataFrame to CSV
    
    Args:
        df (DataFrame): DataFrame to export
        
    Returns:
        bytes: CSV file as bytes
    """
    # Format the DataFrame for export
    export_df = format_products_for_export(df)
    
    # Convert to CSV
    return export_df.to_csv(index=False).encode('utf-8')

def verify_export_functionality(test_data=None):
    """
    Verify that export functionality works correctly
    
    Args:
        test_data: Test DataFrame (optional)
        
    Returns:
        tuple: (success, message)
    """
    try:
        if test_data is None:
            # Create a simple test dataframe
            import pandas as pd
            test_data = pd.DataFrame([
                {
                    'id': 1,
                    'product_name': 'Test Product',
                    'item_sku': 'TST-001',
                    'parent_child': 'Parent',
                    'parent_sku': None,
                    'size': 'M',
                    'color': 'Blue',
                    'image_url': f"https://test-bucket.s3.us-east-1.amazonaws.com/mockups/test_{uuid.uuid4()}.png",
                    'marketplace_title': 'Test Product Title',
                    'category': 'Test Category',
                    'tax_class': 'Standard',
                    'quantity': 10,
                    'price': 19.99,
                    'created_at': pd.Timestamp.now()
                }
            ])
        
        # Try export
        csv_data = export_to_csv(test_data)
        
        # Verify the CSV data
        if not csv_data:
            return False, "Export function returned empty data"
            
        # Try reading CSV back as DataFrame
        import io
        df_back = pd.read_csv(io.StringIO(csv_data.decode('utf-8')))
        
        # Check required columns
        required_columns = [
            'Product Name', 'Item SKU', 'Parent/Child', 'Size', 
            'Colour', 'Image URL', 'Qty', 'Price'
        ]
        
        missing_columns = [col for col in required_columns if col not in df_back.columns]
        
        if missing_columns:
            return False, f"Export is missing required columns: {', '.join(missing_columns)}"
            
        return True, "Export functionality test passed"
    except Exception as e:
        return False, f"Error testing export: {e}"
