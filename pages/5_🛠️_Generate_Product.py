import streamlit as st
import os
import requests
import json
from dotenv import load_dotenv
from utils.database import get_database_connection
from utils.s3_storage import upload_image_file_to_s3, check_s3_connection

# Load environment variables from . 
load_dotenv()


db = get_database_connection()

# Initialize session state for delete confirmation
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
if 'product_to_delete' not in st.session_state:
    st.session_state.product_to_delete = None
if 'mockup_results' not in st.session_state:
    st.session_state.mockup_results = None

# Get all products from database
products_df = db.get_all_products()
print(products_df)

# Initialize session state for selected product
if 'selected_product_id' not in st.session_state:
    st.session_state.selected_product_id = None
if 'selected_product_data' not in st.session_state:
    st.session_state.selected_product_data = None

# Define the available options for sizes and colors
AVAILABLE_SIZES = ["Small", "Medium", "Large", "XL", "2XL"]
AVAILABLE_COLORS = ["Black", "Navy", "Grey", "White", "Red"]

def generate_mockup(image_url, colors, mockup_id=None, smart_object_uuid=None):
    """
    Generate multiple mockups using the Dynamic Mockups API
    
    Args:
        image_url (str): URL of the image uploaded to S3
        colors (list): List of colors for the mockups in hex format
        mockup_id (str): Optional mockup ID to use (from selected product)
        smart_object_uuid (str): Optional smart object UUID to use (from selected product)
        
    Returns:
        list: List of mockup data if successful, empty list otherwise
    """

    # Use provided IDs or fall back to defaults
    MOCKUP_UUID = mockup_id or "db90556b-96a3-483c-ba88-557393b992a1"
    SMART_OBJECT_UUID = smart_object_uuid or "fb677f24-3dce-4d53-b024-26ea52ea43c9"
    
    # Validate input parameters
    if not image_url:
        st.error("No image URL provided for mockup generation")
        return []
        
    # Format validation - make sure the URL is accessible
    try:
        # Check if the image URL is accessible
        image_check = requests.head(image_url)
        if image_check.status_code != 200:
            st.error(f"Image URL is not accessible: {image_url}")
            st.error(f"Status code: {image_check.status_code}")
            return []
    except Exception as e:
        st.error(f"Error validating image URL: {e}")
        return []
    
    # Generate mockups for each color
    mockup_results = []
    
    for color in colors:
        # Create request data according to API documentation format
        request_data = {
            "mockup_uuid": MOCKUP_UUID,
            "smart_objects": [
                {
                    "uuid": SMART_OBJECT_UUID,
                    "color": color,  # For colored objects
                    "asset": {
                        "url": image_url  # Image URL nested inside the asset object
                    }
                }
            ],
            "format": "png",
            "width": 1500,
            "transparent_background": True
        }
        
        st.info(f"Generating mockup with color: {color}")
        st.code(json.dumps(request_data, indent=2))
        
        try:
            response = requests.post(
                'https://app.dynamicmockups.com/api/v1/renders',
                json=request_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'x-api-key': os.getenv('DYNAMIC_MOCKUPS_API_KEY'),
                },
            )
            
            if response.status_code != 200:
                st.error(f"API returned error status: {response.status_code}")
                st.error(f"Response content: {response.text}")
                continue
                
            result = response.json()
            
            # Debug output
            st.success(f"API Response Status Code: {response.status_code}")
            st.code(json.dumps(result, indent=2))
            
            # Get the rendered image URL from the response
            if 'data' in result and 'export_path' in result['data']:
                # Create a mockup result with the expected key
                mockup_data = {
                    'rendered_image_url': result['data']['export_path'],
                    'color': color
                }
                mockup_results.append(mockup_data)
            else:
                st.error("Expected 'data.export_path' in API response but it was not found")
                
        except Exception as e:
            st.error(f"Error generating mockup: {e}")
    
    return mockup_results

def color_name_to_hex(color_name):
    """
    Convert common color names to their hex values
    """
    color_map = {
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
    return color_map.get(color_name, "#FF0000")  # Default to red if color not found

def hex_to_color_name(hex_color):
    """Convert a hex color value to a color name"""
    # Remove # if present
    hex_color = hex_color.upper().lstrip('#')
    
    # Create reverse mapping of color_map
    hex_to_name = {
        "000000": "Black",
        "FFFFFF": "White", 
        "000080": "Navy",
        "808080": "Grey",
        "FF0000": "Red",
        "0000FF": "Blue",
        "008000": "Green",
        "FFFF00": "Yellow",
        "800080": "Purple"
    }
    
    return hex_to_name.get(hex_color, None)

def load_product_data():
    """Load product data if an item is selected from the dropdown"""
    if st.session_state.product_selector and st.session_state.product_selector != "None":
        selected_id = int(st.session_state.product_selector)
        st.session_state.selected_product_id = selected_id
        
        # Fetch the product data from database
        product_data = db.get_product(selected_id)
        if product_data:
            st.session_state.selected_product_data = product_data
            
            # Try to parse JSON string data for sizes and colors
            try:
                if product_data['size'] and product_data['size'].startswith('['):
                    st.session_state.parsed_sizes = json.loads(product_data['size'])
                else:
                    st.session_state.parsed_sizes = []
                    
                if product_data['color'] and product_data['color'].startswith('['):
                    st.session_state.parsed_colors = json.loads(product_data['color'])
                else:
                    st.session_state.parsed_colors = []
            except json.JSONDecodeError:
                st.error("Failed to parse product size or color data")
                st.session_state.parsed_sizes = []
                st.session_state.parsed_colors = []
        else:
            st.error(f"Failed to fetch product with ID {selected_id}")
            st.session_state.selected_product_data = None
    else:
        st.session_state.selected_product_id = None
        st.session_state.selected_product_data = None

def get_valid_sizes_from_parsed(parsed_sizes):
    """Extract valid size names that match our available options"""
    if not parsed_sizes:
        return []
    
    # Create a case-insensitive lookup for matching
    size_lookup = {s.lower(): s for s in AVAILABLE_SIZES}
    
    valid_sizes = []
    for size in parsed_sizes:
        if 'name' in size:
            # Try to find a case-insensitive match
            size_name = size['name']
            if size_name in AVAILABLE_SIZES:
                valid_sizes.append(size_name)
            elif size_name.lower() in size_lookup:
                valid_sizes.append(size_lookup[size_name.lower()])
    
    return valid_sizes

def get_valid_colors_from_parsed(parsed_colors):
    """Extract valid color names that match our available options"""
    if not parsed_colors:
        return []
    
    valid_colors = []
    
    # Check if parsed_colors is a list of strings (hex values)
    if isinstance(parsed_colors, list) and all(isinstance(c, str) for c in parsed_colors):
        # This is the new format - a list of hex values
        for hex_value in parsed_colors:
            # Try to find color name from hex
            color_name = hex_to_color_name(hex_value)
            if color_name and color_name in AVAILABLE_COLORS:
                valid_colors.append(color_name)
    else:
        # This is the old format - a list of objects with name property
        # Create a case-insensitive lookup for matching
        color_lookup = {c.lower(): c for c in AVAILABLE_COLORS}
        
        for color in parsed_colors:
            if isinstance(color, dict) and 'name' in color:
                # Try to find a case-insensitive match
                color_name = color['name']
                if color_name in AVAILABLE_COLORS:
                    valid_colors.append(color_name)
                elif color_name.lower() in color_lookup:
                    valid_colors.append(color_lookup[color_name.lower()])
    
    return valid_colors

# Initialize session state for tracking preview dropdown colors
if 'preview1_selected_color' not in st.session_state:
    st.session_state.preview1_selected_color = None
if 'preview2_selected_color' not in st.session_state:
    st.session_state.preview2_selected_color = None
if 'preview3_selected_color' not in st.session_state:
    st.session_state.preview3_selected_color = None

def generate_product_page():
    st.title("Generate Product")

    # Create a product selector dropdown with all product names and IDs
    # Convert the products dataframe to a dictionary for the selector
    if not products_df.empty and 'id' in products_df.columns and 'product_name' in products_df.columns:
        product_options = {"None": "None"}
        for _, row in products_df.iterrows():
            product_options[str(row['id'])] = f"{row['product_name']} (ID: {row['id']})"
        
        # Product selector dropdown
        st.selectbox(
            "Select a Product",
            options=list(product_options.keys()),
            format_func=lambda x: product_options[x],
            key="product_selector",
            on_change=load_product_data
        )
        
        # Display selected product info
        if st.session_state.selected_product_data:
            product = st.session_state.selected_product_data
            st.success(f"Selected: {product['product_name']}")
            with st.expander("Product Details"):
                st.json(product)
    else:
        st.warning("No products available in the database")

    # Layout with two columns: inputs on the left, preview on the right
    left_col, right_col = st.columns([1, 2])

    with left_col:
        # Input fields - pre-populated with selected product data if available
        default_design_name = ""
        default_marketplace_title = ""
        default_design_sku = "324234"  # Fixed value as in original
        default_sizes = []
        default_colors = []
        
        # Use product data if available
        if st.session_state.selected_product_data:
            product = st.session_state.selected_product_data
            default_design_name = product['product_name']
            default_marketplace_title = product['marketplace_title'] or ""
            default_design_sku = product['item_sku'] or default_design_sku
            
            # Handle sizes - extract from parsed JSON if available and ensure they match available options
            if hasattr(st.session_state, 'parsed_sizes'):
                default_sizes = get_valid_sizes_from_parsed(st.session_state.parsed_sizes)
            
            # Handle colors - extract from parsed JSON if available and ensure they match available options
            if hasattr(st.session_state, 'parsed_colors'):
                default_colors = get_valid_colors_from_parsed(st.session_state.parsed_colors)
                
                # If we still don't have valid colors, show the raw hex values as a reference
                if not default_colors and st.session_state.parsed_colors:
                    st.info("Colors from product record (hex values):")
                    for hex_color in st.session_state.parsed_colors:
                        if isinstance(hex_color, str) and hex_color.startswith('#'):
                            st.markdown(
                                f"<div style='display:flex;align-items:center;'>"
                                f"<div style='width:20px;height:20px;background-color:{hex_color};margin-right:10px;border:1px solid #ccc;'></div>"
                                f"<span>{hex_color}</span>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
        
        # Input fields with defaults from selected product
        design_name = st.text_input("Design Name", value=default_design_name, placeholder="Value")
        marketplace_title = st.text_input("Marketplace Title (80 character limit)", value=default_marketplace_title, placeholder="Value")
        design_sku = st.text_input("Design SKU", value=default_design_sku, disabled=True)

        # Multi-select for sizes and colors - using our defined constants
        sizes = st.multiselect("Select Sizes", AVAILABLE_SIZES, default=default_sizes)
        
        # Colors multiselect with defaults
        colors = st.multiselect("Select Colours", AVAILABLE_COLORS, default=default_colors)

        # Display color hex values for reference
        if colors:
            st.write("Selected Colors:")
            color_cols = st.columns(min(4, len(colors)))
            for i, color in enumerate(colors):
                hex_value = color_name_to_hex(color)
                with color_cols[i % len(color_cols)]:
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='width:30px;height:30px;background-color:{hex_value};margin:0 auto 5px;border:1px solid #ccc;border-radius:4px;'></div>"
                        f"<div style='font-size:0.8em;'>{color}<br>{hex_value}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        # File uploader for design image
        design_image = st.file_uploader("Design Image", type=["png", "jpg", "jpeg"])

        # Show mockup ID and smart object UUID if available
        if st.session_state.selected_product_data and st.session_state.selected_product_data.get('mockup_id'):
            st.info(f"Using Mockup ID: {st.session_state.selected_product_data['mockup_id']}")
        
        if st.session_state.selected_product_data and st.session_state.selected_product_data.get('smart_object_uuid'):
            st.info(f"Using Smart Object UUID: {st.session_state.selected_product_data['smart_object_uuid']}")

        # Single Generate button that handles both product creation and mockup generation
        if st.button("Generate Product"):
            if not design_image:
                st.error("Please upload a design image to generate a product and mockup.")
                return
                
            # First generate the product
            st.success("Product generated successfully!")
            
            # Validate we have all required data
            if not colors:
                st.warning("No colors selected. Using default color (Red).")
                selected_colors = ["Red"]
            else:
                selected_colors = colors
            
            # Step 1: Upload image to S3
            with st.spinner("Uploading image to S3..."):
                image_url = upload_image_file_to_s3(design_image, folder="original")
                
                # Ensure the S3 upload was successful before proceeding
                if not image_url:
                    st.error("Failed to upload image to S3. Please check your AWS configuration.")
                    return
                    
                # Store the uploaded image URL for possible on-demand mockup generation later
                st.session_state.uploaded_image_url = image_url
                
                # Success! Show the uploaded image URL
                st.success("✅ Image uploaded to S3")
                st.info(f"Image URL: {image_url}")
            
            # Step 2: Now that we have a valid image URL from S3, generate mockups for all colors
            with st.spinner("Generating mockups with the uploaded image..."):
                # Convert color names to hex format
                color_hex_list = [color_name_to_hex(color) for color in selected_colors]
                st.info(f"Generating mockups for colors: {', '.join(selected_colors)}")
                
                # Get mockup ID and smart object UUID from selected product if available
                mockup_id = None
                smart_object_uuid = None
                if st.session_state.selected_product_data:
                    mockup_id = st.session_state.selected_product_data.get('mockup_id')
                    smart_object_uuid = st.session_state.selected_product_data.get('smart_object_uuid')
                
                # Call the mockup generation with the S3 image URL and all colors
                mockup_results = generate_mockup(
                    image_url, 
                    color_hex_list,
                    mockup_id=mockup_id,
                    smart_object_uuid=smart_object_uuid
                )
                
                # Store the mockup results in session state for display in the preview section
                if mockup_results:
                    # Create a dictionary mapping hex colors to their rendered URLs for easier lookup
                    mockup_dict = {mockup['color']: mockup['rendered_image_url'] for mockup in mockup_results}
                    st.session_state.mockup_results = mockup_dict
                    
                    # Set the preview colors to the first few generated colors for immediate display
                    generated_colors = []
                    for mockup in mockup_results:
                        hex_color = mockup['color']
                        color_name = next((name for name, hex_val in 
                                        {color: color_name_to_hex(color) for color in selected_colors}.items() 
                                        if hex_val == hex_color), "Unknown")
                        generated_colors.append(color_name)
                    
                    # Set the first 3 colors (or fewer if less were generated)
                    if len(generated_colors) > 0:
                        st.session_state.preview1_selected_color = generated_colors[0]
                    if len(generated_colors) > 1:
                        st.session_state.preview2_selected_color = generated_colors[1]
                    if len(generated_colors) > 2:
                        st.session_state.preview3_selected_color = generated_colors[2]
                    
                    # Success! Show the generated mockups
                    st.success(f"✅ Generated {len(mockup_results)} mockups successfully!")
                    
                    # Display the mockups in a grid
                    mockup_cols = st.columns(min(3, len(mockup_results)))
                    for i, mockup in enumerate(mockup_results):
                        col_idx = i % len(mockup_cols)
                        with mockup_cols[col_idx]:
                            # Find the color name from the hex value
                            color_name = next((name for name, hex_val in 
                                             {color: color_name_to_hex(color) for color in selected_colors}.items() 
                                             if hex_val == mockup['color']), "Unknown")
                            
                            st.image(
                                mockup['rendered_image_url'], 
                                caption=f"Mockup - {color_name}",
                                use_column_width=True
                            )
                else:
                    st.error("Failed to generate any mockups. See error details above.")
                    st.session_state.mockup_results = None

    with right_col:
        # Preview by color
        st.write("### Preview by Colour")
        
        # Check if we have mockups to display
        if st.session_state.mockup_results:
            # Get all generated mockups
            available_mockup_colors = list(st.session_state.mockup_results.keys())
            available_mockup_names = []
            
            # Map hex colors to color names for better display
            for hex_color in available_mockup_colors:
                color_name = hex_to_color_name(hex_color.lstrip('#'))
                available_mockup_names.append(color_name or "Unknown")
            
            st.success(f"Showing all {len(available_mockup_colors)} generated mockups")
            
            # Determine the number of columns for display
            # Calculate columns based on number of mockups (2 columns for 2 mockups, 3 columns for 3-4, 4 for more)
            if len(available_mockup_colors) <= 2:
                num_cols = len(available_mockup_colors)
            elif len(available_mockup_colors) <= 4:
                num_cols = 3
            else:
                num_cols = 4
                
            # Ensure we have at least 1 column
            num_cols = max(1, num_cols)
            
            # Create columns for mockup display
            mockup_cols = st.columns(num_cols)
            
            # Loop through all mockups and display them in the columns
            for i, (hex_color, color_name) in enumerate(zip(available_mockup_colors, available_mockup_names)):
                col_idx = i % num_cols
                with mockup_cols[col_idx]:
                    st.selectbox(
                        f"Color {i+1}", 
                        colors if colors else AVAILABLE_COLORS,
                        index=colors.index(color_name) if color_name in colors else 0,
                        key=f"preview{i}_color",
                        on_change=on_color_change,
                        args=(f"preview{i}",),
                        disabled=True  # Disable changing colors for already generated mockups
                    )
                    
                    # Display the mockup image
                    st.image(
                        st.session_state.mockup_results[hex_color],
                        caption=f"{color_name} ({hex_color})",
                        use_column_width=True
                    )
                    
                    # Add a small gap after each image for better visual separation
                    st.write("")
        else:
            st.info("Generate a product to see mockups here")
            
            # Create 3 columns for color selection dropdowns
            col1, col2, col3 = st.columns(3)
            
            # Only show colors that were selected for the product
            available_colors = colors if colors else AVAILABLE_COLORS
            
            with col1:
                color1 = st.selectbox(
                    "Select Color 1", 
                    available_colors,
                    key="preview1_color",
                    on_change=on_color_change,
                    args=("preview1",)
                )
                
                # Show placeholder if no mockup available yet
                if design_image:
                    st.image(design_image, width=150, caption=f"{color1} (Preview Only)")
                    if st.session_state.uploaded_image_url:
                        if st.button("Generate Mockup", key="gen_mockup1"):
                            generate_on_demand_mockup(color1)
                else:
                    st.image("https://via.placeholder.com/150", width=150, caption=color1)
            
            with col2:
                color2 = st.selectbox(
                    "Select Color 2", 
                    available_colors,
                    key="preview2_color",
                    on_change=on_color_change,
                    args=("preview2",)
                )
                
                # Show placeholder if no mockup available yet
                if design_image:
                    st.image(design_image, width=150, caption=f"{color2} (Preview Only)")
                    if st.session_state.uploaded_image_url:
                        if st.button("Generate Mockup", key="gen_mockup2"):
                            generate_on_demand_mockup(color2)
                else:
                    st.image("https://via.placeholder.com/150", width=150, caption=color2)
            
            with col3:
                color3 = st.selectbox(
                    "Select Color 3", 
                    available_colors,
                    key="preview3_color",
                    on_change=on_color_change,
                    args=("preview3",)
                )
                
                # Show placeholder if no mockup available yet
                if design_image:
                    st.image(design_image, width=150, caption=f"{color3} (Preview Only)")
                    if st.session_state.uploaded_image_url:
                        if st.button("Generate Mockup", key="gen_mockup3"):
                            generate_on_demand_mockup(color3)
                else:
                    st.image("https://via.placeholder.com/150", width=150, caption=color3)
        
        # Remove the separate "All Generated Mockups" expander since we're now showing all mockups directly

# Initialize session state for color selection and on-demand mockup generation
if 'mockup_results' not in st.session_state:
    st.session_state.mockup_results = None
if 'on_demand_colors' not in st.session_state:
    st.session_state.on_demand_colors = []
if 'uploaded_image_url' not in st.session_state:
    st.session_state.uploaded_image_url = None

def generate_on_demand_mockup(color_name):
    """Generate a mockup for a specific color on-demand when selected from dropdown"""
    if not st.session_state.uploaded_image_url:
        st.warning("Please upload an image first before generating mockups.")
        return False
        
    # Convert color name to hex
    hex_color = color_name_to_hex(color_name)
    
    # Check if we already have this color mockup
    if st.session_state.mockup_results and hex_color in st.session_state.mockup_results:
        # We already have this mockup, no need to generate again
        return True
        
    # Get mockup ID and smart object UUID from selected product if available
    mockup_id = None
    smart_object_uuid = None
    if st.session_state.selected_product_data:
        mockup_id = st.session_state.selected_product_data.get('mockup_id')
        smart_object_uuid = st.session_state.selected_product_data.get('smart_object_uuid')
    
    with st.spinner(f"Generating mockup for {color_name}..."):
        # Generate mockup for this specific color
        mockup_results = generate_mockup(
            st.session_state.uploaded_image_url,
            [hex_color],
            mockup_id=mockup_id,
            smart_object_uuid=smart_object_uuid
        )
        
        # Add the new mockup to our session state dictionary
        if mockup_results:
            if not st.session_state.mockup_results:
                st.session_state.mockup_results = {}
                
            st.session_state.mockup_results[hex_color] = mockup_results[0]['rendered_image_url']
            st.success(f"Generated mockup for {color_name}")
            return True
        else:
            st.error(f"Failed to generate mockup for {color_name}")
            return False

def on_color_change(key_prefix):
    """Callback for when a color is changed in dropdown"""
    color_key = f"{key_prefix}_color"
    if color_key in st.session_state:
        selected_color = st.session_state[color_key]
        generate_on_demand_mockup(selected_color)

# Call the function to render the page
generate_product_page()