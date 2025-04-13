import streamlit as st
import pandas as pd
import json
from utils.auth import check_password
from utils.database import get_database_connection
from utils.export import export_to_csv
import datetime

# Verify authentication
if not check_password():
    st.stop()

# Page configuration
st.title("📤 Export Products")

# Initialize database connection
db = get_database_connection()

# Get all products from database
products_df = db.get_all_products()

if products_df.empty:
    st.info("No products found to export. Please add products first.")
else:
    # Add filters for export
    st.subheader("Export Options")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        filter_option = st.selectbox(
            "Filter products",
            options=["All Products", "By Parent/Child", "By Category", "By Date Range"]
        )
    
    filtered_df = products_df.copy()
    
    if filter_option == "By Parent/Child":
        parent_child_filter = st.selectbox(
            "Select type",
            options=["All", "Parent", "Child"]
        )
        
        if parent_child_filter != "All":
            filtered_df = filtered_df[filtered_df['parent_child'] == parent_child_filter]
    
    elif filter_option == "By Category":
        if 'category' in filtered_df.columns:
            categories = ["All"] + sorted(filtered_df['category'].dropna().unique().tolist())
            category_filter = st.selectbox("Select category", options=categories)
            
            if category_filter != "All":
                filtered_df = filtered_df[filtered_df['category'] == category_filter]
    
    elif filter_option == "By Date Range":
        if 'created_at' in filtered_df.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_dtype(filtered_df['created_at']):
                filtered_df['created_at'] = pd.to_datetime(filtered_df['created_at'])
            
            min_date = filtered_df['created_at'].min().date()
            max_date = filtered_df['created_at'].max().date()
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Start date", min_date)
            
            with col2:
                end_date = st.date_input("End date", max_date)
            
            filtered_df = filtered_df[
                (filtered_df['created_at'].dt.date >= start_date) & 
                (filtered_df['created_at'].dt.date <= end_date)
            ]
    
    # Preview the data to export
    st.subheader("Preview Export Data")
    
    # Show a preview of the data
    display_cols = ['id', 'product_name', 'item_sku', 'parent_child', 'price']
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "id": "ID",
            "product_name": "Product Name",
            "item_sku": "SKU",
            "parent_child": "Type",
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
        },
        use_container_width=True
    )
    
    st.write(f"Found {len(filtered_df)} products matching your criteria.")
    
    # Process size and color data for CSV formatting
    export_df = filtered_df.copy()
    
    # Format size column if exists
    if 'size' in export_df.columns:
        def format_size(size_str):
            if pd.isna(size_str) or size_str == '':
                return ''
            try:
                # Handle if it's a JSON string
                if isinstance(size_str, str):
                    sizes = json.loads(size_str)
                    if isinstance(sizes, list):
                        return ','.join([item['name'] for item in sizes if 'name' in item])
                    return size_str
                return str(size_str)
            except:
                return str(size_str)
        
        export_df['size'] = export_df['size'].apply(format_size)
    
    # Format color column if exists
    if 'colour' in export_df.columns:
        def format_color(color_str):
            if pd.isna(color_str) or color_str == '':
                return ''
            try:
                # Handle if it's a JSON string
                if isinstance(color_str, str):
                    # Remove extra quotes and brackets
                    if color_str.startswith('[') or color_str.startswith('{'):
                        colors = json.loads(color_str)
                        if isinstance(colors, list):
                            # Clean up each color code by removing extra quotes
                            cleaned_colors = [c.replace('"', '') for c in colors]
                            return ','.join(cleaned_colors)
                    # Clean up the string directly if it already looks like a formatted array
                    elif '["' in color_str or '""' in color_str:
                        # Remove brackets, extra quotes and spaces
                        cleaned_str = color_str.replace('[', '').replace(']', '').replace('"', '').replace(' ', '')
                        return cleaned_str
                # If it's not a string that needs processing, return as is
                return str(color_str)
            except:
                return str(color_str)
        
        export_df['colour'] = export_df['colour'].apply(format_color)
    
    # Also handle 'color' column if it exists (alternative spelling)
    if 'color' in export_df.columns:
        def format_color(color_str):
            if pd.isna(color_str) or color_str == '':
                return ''
            try:
                # Handle if it's a JSON string
                if isinstance(color_str, str):
                    # Remove extra quotes and brackets
                    if color_str.startswith('[') or color_str.startswith('{'):
                        colors = json.loads(color_str)
                        if isinstance(colors, list):
                            # Clean up each color code by removing extra quotes
                            cleaned_colors = [c.replace('"', '') for c in colors]
                            return ','.join(cleaned_colors)
                    # Clean up the string directly if it already looks like a formatted array
                    elif '["' in color_str or '""' in color_str:
                        # Remove brackets, extra quotes and spaces
                        cleaned_str = color_str.replace('[', '').replace(']', '').replace('"', '').replace(' ', '')
                        return cleaned_str
                # If it's not a string that needs processing, return as is
                return str(color_str)
            except:
                return str(color_str)
        
        export_df['color'] = export_df['color'].apply(format_color)
    
    # Export button
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"product_export_{timestamp}.csv"
    
    csv_data = export_to_csv(export_df)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=export_filename,
            mime="text/csv",
            use_container_width=True
        )
    
    # Show export format info
    st.subheader("Export Format Information")
    st.markdown("""
    The exported CSV file follows this column structure:
    
    - **Product Name**: Name of the product
    - **Item SKU**: Unique product identifier
    - **Parent/Child**: Whether this is a parent or child product
    - **Parent SKU**: For child products, the SKU of the parent
    - **Size**: Product size (if applicable)
    - **Colour**: Product color
    - **Image URL**: URL to the product image (AWS S3 URL if cloud storage is enabled)
    - **Marketplace Title**: Full product title for marketplace listing
    - **Woocommerce Product Category**: Category path
    - **Tax Class**: Tax classification
    - **Qty**: Quantity in stock
    - **Price**: Product price
    
    > **Note:** With S3 storage enabled, the Image URL field will contain permanent, publicly accessible cloud URLs that can be directly used in e-commerce platforms.
    """)
    
    # New section to explain S3 storage benefits
    st.subheader("Cloud Storage Benefits")
    st.markdown("""
    This application uses **AWS S3** for image storage, which provides several advantages:
    
    1. **Scalability** - Store thousands of product images efficiently
    2. **Reliability** - Highly available, durable storage with 99.999999999% durability
    3. **Cost-effective** - Only pay for what you use, typically pennies per GB for storage
    4. **Performance** - Fast image loading from AWS's global CDN network
    5. **Security** - Images can be secured with permissions while still being accessible to your store
    
    Your exported CSV will contain direct links to these cloud-stored images that you can use in your e-commerce platform without having to re-upload them.
    
    ### How It Works
    
    1. When you upload product images, they're stored in your S3 bucket
    2. Mockups are generated using the DynamicMockups API and also stored in S3
    3. The exported CSV contains direct links to these S3-stored images
    4. Your e-commerce platform can use these links directly - no need to re-upload!
    """)
