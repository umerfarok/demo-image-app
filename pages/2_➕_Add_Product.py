import streamlit as st
import json
import random
import string
from utils.database import get_database_connection
from utils.dynamic_mockups import get_mockups
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

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
        if 'sku' in st.session_state:
            st.session_state.sku = ""

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
    if 'available_sizes' not in st.session_state:
        st.session_state.available_sizes = ["Small", "Medium", "Large", "XL", "XXL", "XXXL"]
    if 'selected_sizes' not in st.session_state:
        st.session_state.selected_sizes = []
    if 'sku' not in st.session_state:
        st.session_state.sku = ""  # Initialize SKU as empty string

    # Initialize session state for mockup selections if not already done
    if 'mockup_selections' not in st.session_state:
        st.session_state.mockup_selections = []
    if 'mockup_ids' not in st.session_state:
        st.session_state.mockup_ids = []

    # Color to hex mapping
    COLOR_HEX_MAP = {
        "Black": "#000000",
        "White": "#FFFFFF",
        "Navy": "#000080",
        "Grey": "#808080",
        "Red": "#FF0000",
        "Blue": "#0000FF",
        "Green": "#008000",
        "Yellow": "#FFFF00",
        "Purple": "#800080"
    }

    # Function to generate product SKU based on name, colors, and sizes
    def generate_product_sku(item_name, colors=None, sizes=None):
        """Generate a SKU based on item name, colors, and sizes"""
        if not item_name:
            return ""
            
        # Remove spaces and convert to uppercase
        clean_name = item_name.replace(" ", "").upper()
        
        # Take the first 3 characters of the name, or fewer if the name is shorter
        name_part = clean_name[:min(3, len(clean_name))]
        
        # Add a dash after the name part
        sku = name_part + "-"
        
        # Add color codes (first letter of each color)
        if colors and len(colors) > 0:
            color_part = ""
            for color_hex in colors:
                # Get the color name from the hex value
                color_name = next((k for k, v in COLOR_HEX_MAP.items() if v == color_hex), "")
                if color_name:
                    color_part += color_name[0]  # First letter of the color
            if color_part:
                sku += color_part + "-"
        
        # Add size information (count of sizes)
        if sizes and len(sizes) > 0:
            sku += f"{len(sizes)}-"
        
        # Add a random alphanumeric string to ensure uniqueness
        sku += ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        
        return sku

    # Function to update SKU based on current item name, colors, and sizes
    def update_sku():
        st.session_state.sku = generate_product_sku(
            st.session_state.item_name, 
            st.session_state.colors, 
            st.session_state.sizes
        )

    # Function to generate random SKU
    def generate_random_sku(prefix="", length=8):
        """Generate a random SKU with specified length using letters and digits"""
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{random_part}" if prefix else random_part

    # Function to add multiple sizes
    def add_sizes():
        st.session_state.sizes = []
        for size in st.session_state.selected_sizes:
            # Create a random SKU for each size
            size_sku = generate_random_sku(prefix=f"{size.lower()[:1]}-", length=6)
            st.session_state.sizes.append({
                'name': size,
                'sku': size_sku
            })
        # Update main product SKU after sizes change
        update_sku()

    # Function to add multiple colors
    def add_colors():
        st.session_state.colors = []
        for color in st.session_state.selected_colors:
            # Only store the hex value, not the color name
            st.session_state.colors.append(COLOR_HEX_MAP.get(color, "#FFFFFF"))
        # Update main product SKU after colors change
        update_sku()
        # Don't reset mockup selections when adding colors

    # Function to update item name and mockup ID when selection changes
    def update_mockup_selection():
        """Update mockup IDs and related data when selection changes"""
        # Store all selected mockups
        if "preview_mockup_selection" in st.session_state:
            st.session_state.mockup_selections = st.session_state.preview_mockup_selection
            
            # Update mockup IDs for all selected mockups
            st.session_state.mockup_ids = []
            for mockup in st.session_state.mockup_selections:
                if mockup and mockup != "":
                    st.session_state.mockup_ids.append(mockup_id_map.get(mockup, ""))
            
            # For backward compatibility, store the first selection as the primary mockup
            if st.session_state.mockup_selections:
                st.session_state.mockup_selection = st.session_state.mockup_selections[0]
                # Set item name to match the selected smart object
                st.session_state.item_name = st.session_state.mockup_selection.split(",")[0] if "," in st.session_state.mockup_selection else st.session_state.mockup_selection
                # Update SKU when mockup selection changes
                update_sku()
            else:
                st.session_state.mockup_selection = ""
                st.session_state.item_name = ""
                st.session_state.mockup_id = ""

    # Function to update item name and SKU
    def update_item_name():
        if "form_item_name" in st.session_state:
            st.session_state.item_name = st.session_state.form_item_name
            # Update SKU when item name changes
            update_sku()

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
            # Get current selections for default value
            current_selections = []
            if "mockup_selections" in st.session_state and st.session_state.mockup_selections:
                # Filter to include only valid options that exist in mockup_options
                current_selections = [m for m in st.session_state.mockup_selections if m in mockup_options]
            
            # Create a multiselect with properly filtered default values
            st.multiselect(
                "Select Mockups (Choose multiple)",
                options=mockup_options,
                default=current_selections,  # Only include valid options
                key="preview_mockup_selection",
                on_change=update_mockup_selection
            )

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
        
        st.text_input("SKU", placeholder="Auto-generated SKU", key="sku", value=st.session_state.sku, disabled=True)

        # Size Section
        st.subheader("Size")
        # Use multiselect for sizes
        st.multiselect(
            "Select Sizes", 
            options=st.session_state.available_sizes,
            default=st.session_state.selected_sizes,
            key="selected_sizes"
        )
        
        size_button = st.form_submit_button("Add Sizes", on_click=add_sizes)

        # Display added sizes
        if st.session_state.sizes:
            st.text_area("Size SKUs", value="\n".join([f"{size['name']} - {size['sku']}" for size in st.session_state.sizes]), height=100)

        # Color Section
        st.subheader("Color")
        # Use multiselect for colors 
        st.multiselect(
            "Select Colors",
            options=list(COLOR_HEX_MAP.keys()),
            key="selected_colors"
        )
        
        # Display color previews
        if "selected_colors" in st.session_state and st.session_state.selected_colors:
            st.write("Color Preview:")
            cols = st.columns(len(st.session_state.selected_colors))
            for i, color in enumerate(st.session_state.selected_colors):
                hex_color = COLOR_HEX_MAP.get(color, "#FFFFFF")
                with cols[i]:
                    st.markdown(f"""
                        <div style="
                            background-color: {hex_color}; 
                            width: 30px; 
                            height: 30px; 
                            border-radius: 5px;
                            border: 1px solid #ddd;
                        "></div>
                        <p>{color}<br>{hex_color}</p>
                    """, unsafe_allow_html=True)
        
        color_button = st.form_submit_button("Add Colors", on_click=add_colors)

        # Display added colors
        if st.session_state.colors:
            st.text_area("Selected Colors", value="\n".join(st.session_state.colors), height=100)

        # Mockup ID display
        st.subheader("Selected Mockups")
        if st.session_state.mockup_selections:
            for i, mockup in enumerate(st.session_state.mockup_selections):
                mockup_id = mockup_id_map.get(mockup, "")
                st.text_input(
                    f"Mockup {i+1}: {mockup}",
                    value=mockup_id,
                    key=f"mockup_id_display_{i}",
                    disabled=True
                )
        else:
            st.info("No mockups selected.")

        # Submit button
        submit_button = st.form_submit_button(label="Save")

    # After form submission, handle the update of item name
    if "form_item_name" in st.session_state and st.session_state.form_item_name != st.session_state.item_name:
        st.session_state.item_name = st.session_state.form_item_name
        # Update SKU when item name changes outside the form context
        update_sku()

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
            # Update SKU when mockup/item selection changes
            update_sku()

    # Process form submission
    if submit_button:
        # Use the mockup selection from the outside form component
        st.session_state.item_name = st.session_state.form_item_name if "form_item_name" in st.session_state else st.session_state.item_name
        
        # Get the current value of sku from the session state 
        item_sku = st.session_state.sku
        
        # If SKU is empty, generate it now
        if not item_sku:
            item_sku = generate_product_sku(st.session_state.item_name, st.session_state.colors, st.session_state.sizes)
        
        # Get all mockup IDs and smart object UUIDs
        selected_mockup_ids = []
        smart_object_uuids = []
        
        for mockup_selection in st.session_state.mockup_selections:
            selected_mockup_id = mockup_id_map.get(mockup_selection, "")
            selected_mockup_name = mockup_selection.split(",")[0] if "," in mockup_selection else mockup_selection
            
            # Look through mockups to find the selected one and extract smart object UUID
            for mockup in mockups:
                mockup_id = mockup.get('id', mockup.get('uuid', ''))
                if mockup_id == selected_mockup_id:
                    # Find the smart object with matching name
                    for so in mockup.get('smart_objects', []):
                        if 'Background' not in so.get('name', '') and so.get('name', '') == selected_mockup_name:
                            smart_object_uuids.append(so.get('uuid', None))
                            break
                    break
            
            selected_mockup_ids.append(selected_mockup_id)
        
        # Store multiple mockups as JSON strings
        mockup_ids_json = json.dumps(selected_mockup_ids)
        smart_object_uuids_json = json.dumps(smart_object_uuids)
        
        # Prepare product data with multiple mockup information
        product_data = {
            'product_name': st.session_state.item_name,
            'item_sku': item_sku,
            'parent_child': 'Parent',
            'parent_sku': None,
            'size': st.session_state.size_name if not st.session_state.sizes else json.dumps(st.session_state.sizes),
            'color': st.session_state.color_name if not st.session_state.colors else json.dumps(st.session_state.colors),
            'mockup_id': selected_mockup_ids[0] if selected_mockup_ids else None,  # Primary mockup ID for backward compatibility
            'mockup_ids': mockup_ids_json,  # Store all selected mockup IDs
            'image_url': None,
            'marketplace_title': None,
            'category': ", ".join(st.session_state.mockup_selections),  # Use all selected mockups for category
            'tax_class': None,
            'quantity': 0,
            'price': 0.0,
            'smart_object_uuid': smart_object_uuids[0] if smart_object_uuids else None,  # Primary smart object UUID
            'smart_object_uuids': smart_object_uuids_json,  # Store all smart object UUIDs
        }

        # Validate required fields
        if not product_data['product_name'] or not product_data['item_sku']:
            st.error("Please fill in the Item Name and SKU fields.")
        elif not product_data['mockup_id']:
            st.error("Please select a mockup.")
        else:
            # Debug: Print product data
            print(f"Product data before saving: {product_data}")  # Debug
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
                    # Usingst.rerun() for compatibility with older Streamlit versions
                    st.rerun()
                else:
                    st.error("Failed to add product. Database returned no product ID.")
            except Exception as e:
                st.error(f"An error occurred while saving the product: {e}")
                st.write("Debug Info:", product_data)