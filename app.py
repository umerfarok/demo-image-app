import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from utils.styles import load_css
from utils.auth import require_auth, clear_local_storage

# Set page configuration
st.set_page_config(
    page_title="Product Generator",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown(load_css(), unsafe_allow_html=True)

# Load configuration
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# Check if user is trying to logout
if st.session_state.get("logout_requested"):
    # Clear both streamlit authenticator and our custom session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Clear browser localStorage
    clear_local_storage()
    st.rerun()

# Authentication handling
if not st.session_state.get("authentication_status"):
    # Show login form
    authenticator.login(location='main')
    # Check authentication status after login attempt
        # Successfully authenticated, save to session state
    if st.session_state.get("authentication_status") is False:
        st.error('Username/password is incorrect')
    elif st.session_state.get("authentication_status") is None:
        st.warning('Please enter your username and password')
    
elif st.session_state.get("authentication_status") is True:
    # User is authenticated, show main app content
    # Add logout button to sidebar
    with st.sidebar:
       
        authenticator.logout('Logout', 'sidebar')
            # st.session_state["logout_requested"] = True
            # st.rerun()
    
    # Main content area (only shown when authenticated)
    st.title("Product Generator Dashboard")

    # Welcome message with card styling
    st.markdown("""
    <div style="background-color: black; color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h2 style="margin-top:0 ">Welcome to the Product Generator</h2>
        <p>This application allows you to:</p>
        <ul>
            <li>Create product mockups using the DynamicMockups API</li>
            <li>Store product information in a database</li>
            <li>Generate product variants with different sizes and colors</li>
            <li>Export product data for upload to e-commerce platforms</li>
        </ul>
        <p>Use the sidebar to navigate between different features of the application.</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick links
    st.subheader("Quick Start")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="stat-card" style="border-left: 5px solid #4e73df;">
            <h3 style="margin-top:0">Add Product</h3>
            <p>Create a new product with mockup</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Add Product", key="add_btn"):
            st.query_params["page"] = "add_product"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="stat-card" style="border-left: 5px solid #1cc88a;">
            <h3 style="margin-top:0">View Products</h3>
            <p>Manage your existing products</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Product List", key="list_btn"):
            st.query_params["page"] = "product_list"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="stat-card" style="border-left: 5px solid #f6c23e;">
            <h3 style="margin-top:0">Export Data</h3>
            <p>Export your products to CSV</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Export", key="export_btn"):
            st.query_params["page"] = "export"
            st.rerun()

    with col4:
        st.markdown("""
        <div class="stat-card" style="border-left: 5px solid #f6c23e;">
            <h3 style="margin-top:0">Generate Products</h3>
            <p>Generate product variants</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Product Generator", key="generate_btn"): 
            st.query_params["page"] = "product_generator"
            st.rerun()

    # Create necessary directories if they don't exist
    if not os.path.exists('images'):
        os.makedirs('images')
