import streamlit as st
import os
from utils.auth import check_password
from utils.database import get_database_connection
from utils.api import save_uploaded_image, generate_mockup
import time

# Verify authentication
if not check_password():
    st.stop()

# Page configuration
st.title("➕ Add Product")

# Initialize database connection
db = get_database_connection()

# Custom CSS for form styling
st.markdown("""
<style>
    .product-form {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
    }
    .required:after {
        content: " *";
        color: red;
    }
</style>
""", unsafe_allow_html=True)

with st.form(key="product_form", clear_on_submit=True):
    st.markdown('<div class="product-form">', unsafe_allow_html=True)
    
    st.subheader("Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        product_name = st.text_input(
            "Product Name", 
            help="Name of the product",
            placeholder="e.g., Vintage Graphic T-shirt"
        )
        st.markdown('<p class="required">Product Name is required</p>', unsafe_allow_html=True)
        
        item_sku = st.text_input(
            "Item SKU",
            help="Stock keeping unit - unique identifier for this product",
            placeholder="e.g., VGT-001"
        )
        st.markdown('<p class="required">Item SKU is required</p>', unsafe_allow_html=True)
    
    with col2:
        parent_child = st.selectbox(
            "Parent/Child",
            options=["Parent", "Child"],
            help="Is this a parent product or a child variant?"
        )
        
        parent_sku = st.text_input(
            "Parent SKU",
            help="Required if this is a child variant",
            placeholder="e.g., VGT-000"
        )
        if parent_child == "Child":
            st.markdown('<p class="required">Parent SKU is required for child products</p>', unsafe_allow_html=True)
    
    st.subheader("Product Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        size = st.selectbox(
            "Size",
            options=["", "XS", "S", "M", "L", "XL", "XXL", "XXXL"],
            help="Product size"
        )
    
    with col2:
        color = st.text_input(
            "Color",
            help="Product color",
            placeholder="e.g., Blue"
        )
    
    with col3:
        tax_class = st.selectbox(
            "Tax Class",
            options=["", "Standard", "Reduced", "Zero"],
            help="Tax classification for this product"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        quantity = st.number_input(
            "Quantity",
            min_value=0,
            value=10,
            help="Inventory quantity"
        )
    
    with col2:
        price = st.number_input(
            "Price",
            min_value=0.0,
            value=19.99,
            format="%.2f",
            help="Product price"
        )
    
    st.subheader("Marketing")
    
    marketplace_title = st.text_area(
        "Marketplace Title",
        help="Full title for marketplace listings",
        placeholder="e.g., Vintage Graphic T-shirt with Distressed Design - 100% Cotton - Unisex"
    )
    
    category = st.text_input(
        "Product Category",
        help="Product category for organization",
        placeholder="e.g., Apparel > T-shirts"
    )
    
    st.subheader("Product Image")
    
    uploaded_file = st.file_uploader(
        "Upload Product Image",
        type=["png", "jpg", "jpeg"],
        help="Upload a high quality image for the mockup"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        template_id = st.selectbox(
            "Mockup Template",
            options=["t-shirt", "hoodie", "mug", "poster", "phone-case"],
            help="Select the product template for the mockup"
        )
    
    # Preview uploaded image if available
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    submit_button = st.form_submit_button(label="Create Product", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle form submission
    if submit_button:
        # Validate required fields
        if not product_name:
            st.error("Product Name is required")
        elif not item_sku:
            st.error("Item SKU is required")
        elif parent_child == "Child" and not parent_sku:
            st.error("Parent SKU is required for child products")
        else:
            # Process image if uploaded
            image_path = None
            mockup_path = None
            
            if uploaded_file:
                with st.spinner("Processing image..."):
                    # Save uploaded image
                    image_path = save_uploaded_image(uploaded_file)
                    
                    # Generate mockup
                    st.info("Generating product mockup...")
                    mockup_path = generate_mockup(image_path, template_id)
                    
                    if mockup_path:
                        st.success("Mockup generated successfully!")
                        st.image(mockup_path, caption="Generated Mockup", use_column_width=True)
                    else:
                        st.error("Failed to generate mockup")
            
            # Prepare product data
            product_data = {
                'product_name': product_name,
                'item_sku': item_sku,
                'parent_child': parent_child,
                'parent_sku': parent_sku if parent_child == "Child" else None,
                'size': size,
                'color': color,
                'image_url': mockup_path,
                'marketplace_title': marketplace_title,
                'category': category,
                'tax_class': tax_class,
                'quantity': quantity,
                'price': price
            }
            
            # Save to database
            with st.spinner("Saving product..."):
                product_id = db.add_product(product_data)
                
                if product_id:
                    st.success(f"Product added successfully with ID: {product_id}")
                    
                    # Add a redirect button to view the product list
                    if st.button("View Product List"):
                        st.experimental_set_query_params(page="product_list")
                        time.sleep(0.1)
                        st.experimental_rerun()
                else:
                    st.error("Failed to save product")
