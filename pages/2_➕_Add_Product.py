import streamlit as st
import os
import json
from utils.database import get_database_connection
from utils.api import save_uploaded_image, generate_mockup, is_s3_url
from utils.s3_storage import get_image_from_s3_url
from utils.dynamic_mockups import get_mockups
import time

# Check if we need to reset the form (after successful submission)
if 'reset_form' in st.session_state and st.session_state.reset_form:
    # Clear the reset flag
    st.session_state.reset_form = False
    
    # Clear session state for the form fields
    # This works because the widgets haven't been instantiated yet in this run
    if 'mockup_selection' in st.session_state:
        st.session_state.mockup_selection = ""
    if 'item_name' in st.session_state:
        st.session_state.item_name = ""
    if 'mockup_id' in st.session_state:
        st.session_state.mockup_id = ""
    if 'preview_mockup_selection' in st.session_state:
        st.session_state.preview_mockup_selection = ""

# Initialize session state for sizes, colors, and mockup_id if not already done
if 'sizes' not in st.session_state:
    st.session_state.sizes = []
if 'colors' not in st.session_state:
    st.session_state.colors = []
if 'mockup_id' not in st.session_state:
    st.session_state.mockup_id = ""  # Initialize as empty string
if 'mockup_selection' not in st.session_state:
    st.session_state.mockup_selection = ""  # Initialize dropdown as empty string
if 'item_name' not in st.session_state:
    st.session_state.item_name = ""  # Initialize item name as empty string
if 'preview_mockup_selection' not in st.session_state:
    st.session_state.preview_mockup_selection = ""  # Initialize preview selection

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

# Function to update item name and mockup ID when selection changes
def update_mockup_selection():
    selected_mockup = st.session_state.mockup_selection
    if selected_mockup and selected_mockup != "":
        st.session_state.mockup_id = mockup_id_map.get(selected_mockup, "")
        # Set item name to match the selected smart object
        st.session_state.item_name = selected_mockup.split(",")[0] if "," in selected_mockup else selected_mockup
    else:
        st.session_state.mockup_id = ""
        st.session_state.item_name = ""
    print(f"Updated mockup_id: {st.session_state.mockup_id}")  # Debug
    print(f"Updated item_name: {st.session_state.item_name}")  # Debug

# Fetch mockups from API
mockups = get_mockups()
print(f"Mockups fetched: {mockups}")  # Debugging line

# Create descriptive options for the mockup selection
mockup_options = [""]  # Start with an empty option
mockup_id_map = {}  # Dictionary to map display text to mockup ID

for mockup in mockups:
    print(f"Processing mockup: {mockup}")  # Debug
    smart_objects_info = []
    for so in mockup.get('smart_objects', []):
        if 'Background' not in so.get('name', ''):  # Skip background objects
            smart_objects_info.append(so.get('name', 'Unnamed'))
    
    smart_objects_text = ", ".join(smart_objects_info) if smart_objects_info else "No printable objects"
    option_text = f"{smart_objects_text}"
    mockup_options.append(option_text)
    
    # Store the mapping between option text and mockup ID
    mockup_id = mockup.get('id', mockup.get('uuid', ''))  # Try 'id' first, then 'uuid'
    print(f"Mapping '{option_text}' to ID: {mockup_id}")
    mockup_id_map[option_text] = mockup_id

# Create a function to handle mockup selection outside the form
def handle_mockup_selection():
    # Create a container for the selection outside the form
    selection_container = st.container()
    
    with selection_container:
        # Create a selectbox outside the form to handle the selection change immediately
        st.selectbox(
            "Select Mockup",
            options=mockup_options,
            index=mockup_options.index(st.session_state.mockup_selection) if st.session_state.mockup_selection in mockup_options else 0,
            key="preview_mockup_selection",
            on_change=update_mockup_selection
        )
        
        # Update the session state to sync the selection
        if "preview_mockup_selection" in st.session_state:
            st.session_state.mockup_selection = st.session_state.preview_mockup_selection
            
            # Update mockup ID
            if st.session_state.mockup_selection and st.session_state.mockup_selection != "":
                st.session_state.mockup_id = mockup_id_map.get(st.session_state.mockup_selection, "")
                # Set item name to match the selected smart object
                st.session_state.item_name = st.session_state.mockup_selection.split(",")[0] if "," in st.session_state.mockup_selection else st.session_state.mockup_selection
            else:
                st.session_state.mockup_id = ""
                st.session_state.item_name = ""

# Page configuration
st.title("Add Blank Item")

# Display the mockup selection outside the form for immediate updates
handle_mockup_selection()

# Form for adding a blank item
with st.form(key="add_blank_item_form", clear_on_submit=False):
    # Item Name and SKU
    st.subheader("Item Name")
    st.text_input("Item Name", placeholder="Enter item name", value=st.session_state.item_name, key="form_item_name")
    
    # Before form submission, sync the form values with session state
    if "form_item_name" in st.session_state:
        st.session_state.item_name = st.session_state.form_item_name
    
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

    # Mockup ID display
    st.subheader("Mockup Information")
    st.text_input(
        "Mockup UUID",
        value=st.session_state.mockup_id,
        key="mockup_id_display",
        disabled=True
    )

    # Submit button
    submit_button = st.form_submit_button(label="Save")

# Update mockup selection when form is submitted or when page loads
if st.session_state.mockup_selection and st.session_state.mockup_selection != "":
    # Check if mockup_id needs updating based on current selection
    current_mockup_id = mockup_id_map.get(st.session_state.mockup_selection, "")
    if current_mockup_id != st.session_state.mockup_id:
        st.session_state.mockup_id = current_mockup_id
        # Update item name to match the selected smart object
        st.session_state.item_name = (st.session_state.mockup_selection.split(",")[0] 
                                     if "," in st.session_state.mockup_selection 
                                     else st.session_state.mockup_selection)

# Process form submission
if submit_button:
    # Use the mockup selection from the outside form component
    # We're not accessing form_mockup_selection anymore since mockup selection is done outside the form
    st.session_state.item_name = st.session_state.form_item_name if "form_item_name" in st.session_state else st.session_state.item_name
    
    # Get the current value of sku from the session state without modifying it
    item_sku = st.session_state.sku
    
    # Prepare product data
    product_data = {
        'product_name': st.session_state.item_name,  # Use the synced item name
        'item_sku': item_sku,  # Use local variable instead of modifying session state
        'parent_child': 'Parent',
         'parent_sku': None,
        'size': st.session_state.size_name if not st.session_state.sizes else json.dumps(st.session_state.sizes),
        'color': st.session_state.color_name if not st.session_state.colors else json.dumps(st.session_state.colors),
        'mockup_id': st.session_state.mockup_id,
         'image_url': None,
         'marketplace_title': None,
        'category': st.session_state.mockup_selection,  # Use the selected mockup value as category
         'tax_class': None,
         'quantity': 0,
         'price': 0.0,
    }

    # Validate required fields
    if not product_data['product_name'] or not product_data['item_sku']:
        st.error("Please fill in the Item Name and SKU fields.")
    elif not product_data['mockup_id']:
        st.error("Please select a mockup.")
    else:
        # Debug: Print product data
        st.write("Product Data to be saved:", product_data)

        # Add product to database
        db = get_database_connection()
        try:
            product_id = db.add_product(product_data)
            if product_id:
                st.success(f"Product added successfully with ID: {product_id}")
                
                # Store a flag in session state to indicate we should reset on next load
                st.session_state.reset_form = True
                
                # Only reset the data that doesn't belong to active widgets
                st.session_state.sizes = []
                st.session_state.colors = []
                
                # Redirect to refresh the page (which will reset all widgets)
                # Using st.rerun() instead of deprecated st.experimental_rerun()
                st.rerun()
            else:
                st.error("Failed to add product. Database returned no product ID.")
        except Exception as e:
            st.error(f"An error occurred while saving the product: {e}")
            st.write("Debug Info:", product_data)