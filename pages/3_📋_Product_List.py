import streamlit as st
import pandas as pd
import os
from utils.auth import check_password
from utils.database import get_database_connection
from PIL import Image
import io
import requests
from utils.api import is_s3_url
from utils.s3_storage import get_image_from_s3_url

# Verify authentication
if not check_password():
    st.stop()

# Page configuration
st.title("📋 Product List")

# Initialize database connection
db = get_database_connection()

# Initialize session state for delete confirmation
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
if 'product_to_delete' not in st.session_state:
    st.session_state.product_to_delete = None
    
# Initialize session state for viewing a single product
if 'view_product_id' not in st.session_state:
    st.session_state.view_product_id = None

# Initialize pagination state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'items_per_page' not in st.session_state:
    st.session_state.items_per_page = 5

# Get all products from database
products_df = db.get_all_products()

# Handle delete confirmation modal
if st.session_state.confirm_delete:
    product_id = st.session_state.product_to_delete
    product = db.get_product(product_id)
    
    # Create modal-like dialog with warning style
    st.warning("⚠️ Delete Confirmation")
    st.write(f"Are you sure you want to delete **{product['product_name']}**?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete", type="primary"):
            if db.delete_product(product_id):
                st.session_state.confirm_delete = False
                st.session_state.product_to_delete = None
                st.success("Product deleted successfully!")
                # Refresh the page to reflect changes
                st.experimental_rerun()
            else:
                st.error("Failed to delete product")
    with col2:
        if st.button("Cancel"):
            st.session_state.confirm_delete = False
            st.session_state.product_to_delete = None
            st.experimental_rerun()

# Handle view single product
elif st.session_state.view_product_id is not None:
    product_id = st.session_state.view_product_id
    product = db.get_product(product_id)
    
    # Back button
    if st.button("← Back to Product List"):
        st.session_state.view_product_id = None
        st.experimental_rerun()
    
    # Display product details with improved layout
    st.subheader(f"Product Details: {product['product_name']}")
    
    # Create a single column layout for the simplified view
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Format size and color fields
        size_value = 'N/A'
        color_value = 'N/A'
        
        # Process Size field - extract names and join with commas
        if product['size']:
            try:
                import json
                # Try to parse as JSON if it's a string representation of an array
                if isinstance(product['size'], str) and (product['size'].startswith('[') or product['size'].startswith('{')):
                    size_data = json.loads(product['size'])
                    if isinstance(size_data, list):
                        if all(isinstance(item, dict) and 'name' in item for item in size_data):
                            # Extract just the name values from each dictionary
                            size_names = [item['name'] for item in size_data]
                            size_value = ', '.join(size_names)
                        else:
                            # For simple string values in the array
                            size_value = ', '.join(str(item) for item in size_data)
                    else:
                        size_value = str(product['size'])
                else:
                    size_value = str(product['size'])
            except:
                size_value = str(product['size'])
        
        # Process Color field - join array values with commas  
        if product['color']:
            try:
                import json
                # Try to parse as JSON if it's a string representation of an array
                if isinstance(product['color'], str) and product['color'].startswith('['):
                    color_data = json.loads(product['color'])
                    if isinstance(color_data, list):
                        color_value = ', '.join(str(color) for color in color_data)
                    else:
                        color_value = str(product['color'])
                else:
                    color_value = str(product['color'])
            except:
                color_value = str(product['color'])
                
        # Create a dictionary for product details
        product_details = {
            "Product Name": product['product_name'],
            "Size": size_value,
            "Color": color_value,
            "Price": f"${product['price']}",
            "Category": product['category']
        }
        
        # Add created_at if available
        if 'created_at' in product and product['created_at']:
            product_details["Created at"] = product['created_at']
            
        # Convert dictionary to DataFrame for table display
        details_df = pd.DataFrame(product_details.items(), columns=['Attribute', 'Value'])
        st.table(details_df)
    
    with col2:
        # Display product image if available
        if product['image_url']:
            if is_s3_url(product['image_url']):
                # S3 image
                img = get_image_from_s3_url(product['image_url'])
                if img:
                    st.image(img, caption=f"Image for {product['product_name']}", use_column_width=True)
                else:
                    st.markdown("📷 *Image unavailable or could not be loaded*")
            else:
                # Local image
                if os.path.exists(product['image_url']):
                    st.image(product['image_url'], caption=f"Image for {product['product_name']}", use_column_width=True)
                else:
                    st.markdown("📷 *Image file not found*")
        else:
            st.markdown("📷 *No image available*")

else:
    # Add search and filter functionality - Only shown when not viewing a single product
    st.subheader("Search & Filter")

    col1, col2 = st.columns(2)  # Changed from 3 columns to 2

    with col1:
        search_term = st.text_input("Search by name or SKU", "")

    with col2:
        if not products_df.empty and 'category' in products_df.columns:
            categories = products_df['category'].dropna().unique().tolist()
            categories = ["All"] + categories
            category_filter = st.selectbox("Filter by category", categories)
        else:
            category_filter = "All"

    # Add CSV export button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Generate CSV File for All Product"):
            st.session_state.export_all = True
            st.experimental_rerun()

    # Apply filters
    filtered_df = products_df.copy()

    # Ensure numeric columns have proper data types
    if not filtered_df.empty:
        # Convert price to float with error handling
        filtered_df['price'] = pd.to_numeric(filtered_df['price'], errors='coerce').fillna(0.0)
        # Convert quantity to integer with error handling
        filtered_df['quantity'] = pd.to_numeric(filtered_df['quantity'], errors='coerce').fillna(0).astype(int)

    # Search filter
    if search_term:
        search_mask = (
            filtered_df['product_name'].str.contains(search_term, case=False, na=False) | 
            filtered_df['item_sku'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]

    # Category filter
    if category_filter != "All" and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['category'] == category_filter]

    # Display products
    if filtered_df.empty:
        st.info("No products found matching your criteria.")
    else:
        # Calculate pagination values
        total_items = len(filtered_df)
        total_pages = (total_items + st.session_state.items_per_page - 1) // st.session_state.items_per_page
        
        # Ensure current page is valid
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
        if st.session_state.current_page < 1:
            st.session_state.current_page = 1
        
        # Calculate start and end indices for current page
        start_idx = (st.session_state.current_page - 1) * st.session_state.items_per_page
        end_idx = min(start_idx + st.session_state.items_per_page, total_items)
        
        # Get products for the current page
        page_df = filtered_df.iloc[start_idx:end_idx]
        
        # Display custom product table with image, title, and action columns
        st.subheader("Products")
        
        # Create custom table header
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.markdown("**Image**")
        with cols[1]:
            st.markdown("**Product Title**")
        with cols[2]:
            st.markdown("**Action**")
            
        # Add separator line
        st.markdown("<hr style='margin-top: 0; margin-bottom: 10px;'>", unsafe_allow_html=True)
        
        # Iterate through products and display in rows
        for idx, row in page_df.iterrows():
            product_id = row['id']
            product_name = row['product_name']
            
            cols = st.columns([1, 3, 1])
            
            # Image column
            with cols[0]:
                if row['image_url']:
                    if is_s3_url(row['image_url']):
                        # S3 image
                        img = get_image_from_s3_url(row['image_url'])
                        if img:
                            st.image(img, width=70)
                        else:
                            st.markdown("📷")
                    else:
                        # Local image
                        if os.path.exists(row['image_url']):
                            st.image(row['image_url'], width=70)
                        else:
                            st.markdown("📷")
                else:
                    st.markdown("📷")
            
            # Product name column
            with cols[1]:
                st.write(product_name)
            
            # Action column
            with cols[2]:
                view_col, delete_col = st.columns(2)
                
                with view_col:
                    if st.button("View", key=f"view_{product_id}"):
                        st.session_state.view_product_id = product_id
                        st.experimental_rerun()
                
                with delete_col:
                    if st.button("Delete", key=f"delete_{product_id}"):
                        st.session_state.confirm_delete = True
                        st.session_state.product_to_delete = product_id
                        st.experimental_rerun()
            
            # Add separator line between rows
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # Add pagination controls
        st.write("")  # Add some spacing
        
        # Define pagination UI
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            prev_disabled = (st.session_state.current_page <= 1)
            if st.button("← Previous", disabled=prev_disabled, key="prev_button"):
                st.session_state.current_page -= 1
                st.experimental_rerun()
                
        with col2:
            # Show page numbers
            page_numbers = []
            
            # Always show first page
            if st.session_state.current_page > 3:
                page_numbers.append(1)
                if st.session_state.current_page > 4:
                    page_numbers.append("...")
            
            # Show current page and surrounding pages
            for i in range(max(1, st.session_state.current_page - 1), 
                          min(total_pages + 1, st.session_state.current_page + 2)):
                page_numbers.append(i)
            
            # Always show last page
            if st.session_state.current_page < total_pages - 2:
                if st.session_state.current_page < total_pages - 3:
                    page_numbers.append("...")
                page_numbers.append(total_pages)
            
            # Create the page selector
            page_cols = st.columns(len(page_numbers))
            
            for i, page_col in enumerate(page_cols):
                with page_col:
                    if page_numbers[i] == "...":
                        st.write("...")
                    else:
                        page_num = page_numbers[i]
                        if page_num == st.session_state.current_page:
                            # Highlight current page
                            st.markdown(f"**{page_num}**")
                        else:
                            if st.button(f"{page_num}", key=f"page_{page_num}"):
                                st.session_state.current_page = page_num
                                st.experimental_rerun()
        
        with col3:
            next_disabled = (st.session_state.current_page >= total_pages)
            if st.button("Next →", disabled=next_disabled, key="next_button"):
                st.session_state.current_page += 1
                st.experimental_rerun()
        
        # Display page information
        st.write(f"Page {st.session_state.current_page} of {total_pages} | Showing {start_idx+1}-{end_idx} of {total_items} products")
