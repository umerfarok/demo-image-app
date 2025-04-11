import streamlit as st
import os
import json
from utils.auth import check_password
from utils.database import get_database_connection
from utils.api import save_uploaded_image, generate_mockup, is_s3_url
from utils.s3_storage import get_image_from_s3_url
import time

# Verify authentication
if not check_password():
    st.stop()

# Initialize session state for sizes and colors if not already done
if 'sizes' not in st.session_state:
    st.session_state.sizes = []
if 'colors' not in st.session_state:
    st.session_state.colors = []

# Function to add size
def add_size():
    if st.session_state.size_name and st.session_state.size_sku:
        st.session_state.sizes.append({
            'name': st.session_state.size_name,
            'sku': st.session_state.size_sku
        })
        st.session_state.size_name = ""
        st.session_state.size_sku = ""

# Function to add color
def add_color():
    if st.session_state.color_name and st.session_state.color_hex:
        st.session_state.colors.append({
            'name': st.session_state.color_name,
            'hex': st.session_state.color_hex
        })
        st.session_state.color_hex = ""

# Page configuration
st.title("Add Blank Item")

# Create a two-column layout
form_col, preview_col = st.columns([2, 1], gap="large")

# Add Blank Item form in the left column
with form_col:
    # Form for adding a blank item
    with st.form(key="add_blank_item_form", clear_on_submit=False):
        # Item Name and SKU
        st.text_input("Item Name", placeholder="Enter item name", key="item_name")
        st.text_input("SKU", placeholder="Enter SKU", key="sku")

        # Size Section
        st.subheader("Size")
        cols = st.columns([3, 1])
        with cols[0]:
            st.text_input("Size", placeholder="Enter size name", key="size_name")
        with cols[1]:
            st.text_input("Size SKU", placeholder="Enter size SKU", key="size_sku")
        st.form_submit_button("Add Size", on_click=add_size)

        # Display added sizes
        if st.session_state.sizes:
            st.text_area("Size SKU", value="\n".join([f"{size['name']} - {size['sku']}" for size in st.session_state.sizes]), height=100)

        # Color Section
        st.subheader("Color")
        cols = st.columns([3, 1, 1])
        with cols[0]:
            st.selectbox("Color", ["Black", "White", "Navy", "Grey"], key="color_name")
        with cols[1]:
            st.text_input("Hex Colour", placeholder="#FFFFFF", key="color_hex")
        with cols[2]:
            st.form_submit_button("Add Color", on_click=add_color)

        # Display added colors
        if st.session_state.colors:
            st.text_area("Smart Object UUID (for colour)", value="\n".join([color['name'] for color in st.session_state.colors]), height=100)

        # Mockup ID
        st.subheader("Mockup ID")
        st.text_input("Enter Mockup ID (UUID)", placeholder="Enter UUID", key="mockup_id")

        # Submit button
        submit_button = st.form_submit_button(label="Save")
        
# Mockup Views in the right column
with preview_col:
    st.subheader("Mockup Views")
    for i in range(3):  # 3 rows of mockups
        cols = st.columns(3)
        for j, col in enumerate(cols):
            with col:
                st.image("https://via.placeholder.com/150", caption=f"Mockup {i * 3 + j + 1}")
                st.selectbox("Select Colour", ["Black", "White", "Navy", "Grey"], key=f"mockup_color_{i * 3 + j}")

# Process form submission
if submit_button:  # Using the variable directly instead of checking session state
    # Prepare product data
    product_data = {
        'product_name': st.session_state.item_name,
        'item_sku': st.session_state.sku,
        'parent_child': 'Parent',
        'parent_sku': None,
        'size': st.session_state.size_name if not st.session_state.sizes else json.dumps(st.session_state.sizes),
        'color': st.session_state.color_name if not st.session_state.colors else json.dumps(st.session_state.colors),
        'mockup_id': st.session_state.mockup_id,  # Added mockup ID to the data
        'image_url': None,
        'marketplace_title': None,
        'category': None,
        'tax_class': None,
        'quantity': 0,
        'price': 0.0,
    }

    # Validate required fields
    if not product_data['product_name'] or not product_data['item_sku']:
        st.error("Please fill in the Item Name and SKU fields.")
    else:
        # Debug: Print product data to validate
        st.write("Product Data to be saved:", product_data)

        # Add product to database
        db = get_database_connection()
        try:
            product_id = db.add_product(product_data)
            if product_id:
                st.success(f"Product added successfully with ID: {product_id}")
                # Reset form and session state
                st.session_state.sizes = []
                st.session_state.colors = []
                st.session_state.item_name = ""
                st.session_state.sku = ""
                st.session_state.mockup_id = ""
            else:
                st.error("Failed to add product. Database returned no product ID.")
        except Exception as e:
            st.error(f"An error occurred while saving the product: {e}")
            st.write("Debug Info:", product_data)
