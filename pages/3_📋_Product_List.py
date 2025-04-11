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

# Get all products from database
products_df = db.get_all_products()

# Add search and filter functionality
st.subheader("Search & Filter")

col1, col2, col3 = st.columns(3)

with col1:
    search_term = st.text_input("Search by name or SKU", "")

with col2:
    if not products_df.empty and 'parent_child' in products_df.columns:
        product_type_filter = st.selectbox(
            "Filter by type",
            options=["All", "Parent", "Child"],
            index=0
        )
    else:
        product_type_filter = "All"

with col3:
    if not products_df.empty and 'category' in products_df.columns:
        categories = products_df['category'].dropna().unique().tolist()
        categories = ["All"] + categories
        category_filter = st.selectbox("Filter by category", categories)
    else:
        category_filter = "All"

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

# Product type filter
if product_type_filter != "All" and not filtered_df.empty:
    filtered_df = filtered_df[filtered_df['parent_child'] == product_type_filter]

# Category filter
if category_filter != "All" and not filtered_df.empty:
    filtered_df = filtered_df[filtered_df['category'] == category_filter]

# Display products
if filtered_df.empty:
    st.info("No products found matching your criteria.")
else:
    # Display product table with limited columns
    display_cols = ['id', 'product_name', 'item_sku', 'parent_child', 'size', 'color', 'price', 'quantity']
    
    # Ensure all columns are present
    for col in display_cols:
        if col not in filtered_df.columns:
            filtered_df[col] = ""
    
    # Display the table
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "id": "ID",
            "product_name": "Product Name",
            "item_sku": "SKU",
            "parent_child": "Type",
            "size": "Size",
            "color": "Color",
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "quantity": st.column_config.NumberColumn("Quantity", format="%d")
        },
        use_container_width=True
    )
    
    # Product detail view
    st.subheader("Product Details")
    
    # Select a product to view or edit
    selected_product_id = st.selectbox(
        "Select a product to view or edit",
        options=filtered_df['id'].tolist(),
        format_func=lambda x: f"{x} - {filtered_df[filtered_df['id'] == x]['product_name'].iloc[0]}"
    )
    
    # Display selected product details
    if selected_product_id:
        product = db.get_product(selected_product_id)
        
        if product:
            # Create tabs for viewing and editing
            view_tab, edit_tab = st.tabs(["View", "Edit"])
            
            with view_tab:
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.markdown(f"### {product['product_name']}")
                    st.markdown(f"**SKU:** {product['item_sku']}")
                    st.markdown(f"**Type:** {product['parent_child']}")
                    
                    if product['parent_child'] == 'Child':
                        st.markdown(f"**Parent SKU:** {product['parent_sku']}")
                    
                    st.markdown(f"**Size:** {product['size'] or 'N/A'}")
                    st.markdown(f"**Color:** {product['color'] or 'N/A'}")
                    st.markdown(f"**Price:** ${product['price']}")
                    st.markdown(f"**Quantity:** {product['quantity']}")
                    st.markdown(f"**Category:** {product['category'] or 'N/A'}")
                    st.markdown(f"**Tax Class:** {product['tax_class'] or 'N/A'}")
                    
                    if product['marketplace_title']:
                        st.markdown("**Marketplace Title:**")
                        st.markdown(f"*{product['marketplace_title']}*")
                
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
            
            with edit_tab:
                with st.form(key=f"edit_product_{selected_product_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edited_name = st.text_input("Product Name", value=product['product_name'])
                        edited_sku = st.text_input("Item SKU", value=product['item_sku'])
                        edited_parent_child = st.selectbox(
                            "Parent/Child",
                            options=["Parent", "Child"],
                            index=0 if product['parent_child'] == "Parent" else 1
                        )
                        edited_parent_sku = st.text_input("Parent SKU", value=product['parent_sku'] or "")
                    
                    with col2:
                        edited_size = st.text_input("Size", value=product['size'] or "")
                        edited_color = st.text_input("Color", value=product['color'] or "")
                        
                        # Add safe conversion for quantity
                        try:
                            quantity_value = int(product['quantity'])
                        except (ValueError, TypeError):
                            quantity_value = 0
                        edited_quantity = st.number_input("Quantity", value=quantity_value, min_value=0)
                        
                        # Add safe conversion for price
                        try:
                            price_value = float(product['price'])
                        except (ValueError, TypeError):
                            price_value = 0.0
                        edited_price = st.number_input("Price", value=price_value, format="%.2f", min_value=0.0)
                    
                    edited_category = st.text_input("Category", value=product['category'] or "")
                    edited_tax_class = st.text_input("Tax Class", value=product['tax_class'] or "")
                    edited_marketplace_title = st.text_area("Marketplace Title", value=product['marketplace_title'] or "")
                    
                    # Upload new image
                    new_image = st.file_uploader("Upload New Image (leave empty to keep current)", type=["png", "jpg", "jpeg"])
                    
                    submit = st.form_submit_button("Update Product")
                    
                    # Change delete button to a form submit button to trigger confirmation
                    delete = st.form_submit_button("Delete Product", type="primary")
                    
                    if submit:
                        # Handle image upload if provided
                        image_url = product['image_url']
                        
                        # Update product in database
                        updated_product = {
                            'product_name': edited_name,
                            'item_sku': edited_sku,
                            'parent_child': edited_parent_child,
                            'parent_sku': edited_parent_sku if edited_parent_child == "Child" else None,
                            'size': edited_size,
                            'color': edited_color,
                            'image_url': image_url,
                            'marketplace_title': edited_marketplace_title,
                            'category': edited_category,
                            'tax_class': edited_tax_class,
                            'quantity': edited_quantity,
                            'price': edited_price
                        }
                        
                        if db.update_product(selected_product_id, updated_product):
                            st.success("Product updated successfully!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to update product")
                    
                    if delete:
                        # Set session state to show confirmation instead of performing delete directly
                        st.session_state.confirm_delete = True
                        st.session_state.product_to_delete = selected_product_id
                        st.experimental_rerun()
                
                # Delete confirmation - outside the form
                if st.session_state.confirm_delete and st.session_state.product_to_delete == selected_product_id:
                    st.warning("Are you sure you want to delete this product? This action cannot be undone.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete Product"):
                            if db.delete_product(selected_product_id):
                                st.session_state.confirm_delete = False
                                st.session_state.product_to_delete = None
                                st.success("Product deleted successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete product")
                    with col2:
                        if st.button("Cancel"):
                            st.session_state.confirm_delete = False
                            st.session_state.product_to_delete = None
                            st.experimental_rerun()
