import streamlit as st
from utils.auth import check_password
from utils.database import get_database_connection
import pandas as pd
import time

# Verify authentication
if not check_password():
    st.stop()

# Page configuration
st.title("🏠 Dashboard")

# Initialize database connection
db = get_database_connection()

# Get statistics
stats = db.get_stats()

# Display statistics in a nice layout
st.markdown("""
<style>
    .stat-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .stat-card h1 {
        font-size: 2.5rem;
        color: #4e73df;
        margin-bottom: 0.5rem;
    }
    .stat-card p {
        color: #5a5c69;
        font-size: 1rem;
        margin-bottom: 0;
    }
</style>
""", unsafe_allow_html=True)

# Display statistics in cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <h1>{stats['total_products']}</h1>
        <p>Total Products</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <h1>{stats['parent_count']}</h1>
        <p>Parent Products</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <h1>{stats['image_count']}</h1>
        <p>Images Generated</p>
    </div>
    """, unsafe_allow_html=True)

# Recent products
st.subheader("Recent Products")

# Get recent products
products_df = db.get_all_products()

if not products_df.empty:
    # Display recent products (limited to latest 5)
    recent_products = products_df.head(5)
    
    # Format the display columns
    display_cols = ['id', 'product_name', 'item_sku', 'parent_child', 'price', 'created_at']
    display_df = recent_products[display_cols].copy()
    
    # Format the created_at column to a nicer date format
    if 'created_at' in display_df.columns:
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Style the dataframe
    st.dataframe(
        display_df,
        column_config={
            "id": "ID",
            "product_name": "Product Name",
            "item_sku": "SKU",
            "parent_child": "Type",
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "created_at": "Created At"
        },
        use_container_width=True
    )
    
    # Link to product list
    st.write("[View all products →](/Product_List)")
else:
    st.info("No products added yet. [Add your first product](/Add_Product)")

# Quick links
st.subheader("Quick Links")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Add New Product", use_container_width=True):
        st.experimental_set_query_params(page="add_product")
        time.sleep(0.1)  # Short delay to allow query param to take effect
        st.rerun()

with col2:
    if st.button("View All Products", use_container_width=True):
        st.experimental_set_query_params(page="product_list")
        time.sleep(0.1)
        st.rerun()

with col3:
    if st.button("Export Products", use_container_width=True):
        st.experimental_set_query_params(page="export")
        time.sleep(0.1)
        st.rerun()

# App information
st.markdown("""
## About this Application

The Product Generator app helps you:

1. **Create product mockups** using the DynamicMockups API
2. **Store product information** in a database
3. **Generate product variants** with different sizes and colors
4. **Export product data** for upload to e-commerce platforms

Use the sidebar to navigate between different features of the application.
""")
