import pandas as pd

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
