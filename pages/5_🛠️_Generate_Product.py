import streamlit as st
import os
import requests
import json
import random
import string
from dotenv import load_dotenv
from utils.database import get_database_connection
from utils.s3_storage import upload_image_file_to_s3, check_s3_connection
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Load environment variables from . 
load_dotenv()

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

# Function to generate product SKU based on name, colors, sizes, and marketplace title
    def generate_product_sku(design_name, colors=None, sizes=None, marketplace_title=None):
        """Generate a unique SKU based on design name, colors, sizes, and marketplace title"""
        if not design_name:
            return ""
            
        # Remove spaces and convert to uppercase
        clean_name = design_name.replace(" ", "").upper()
        
        # Take the first 3 characters of the design name, or fewer if the name is shorter
        name_part = clean_name[:min(3, len(clean_name))]
        
        # Add marketplace title influence if available (first 2 chars)
        if marketplace_title:
            clean_title = marketplace_title.replace(" ", "").upper()
            title_part = clean_title[:min(2, len(clean_title))]
            name_part = name_part + title_part[:1]  # Add just one character from title to keep SKU compact
        
        # Add a dash after the name part
        sku = name_part + "-"
        
        # Add color codes (first letter of each color)
        if colors and len(colors) > 0:
            color_part = ""
            for color in colors:
                color_part += color[0].upper()  # First letter of each color
            if color_part:
                sku += color_part + "-"
        
        # Add size information (count of sizes)
        if sizes and len(sizes) > 0:
            sku += f"{len(sizes)}-"
        
        # Add a random alphanumeric string to ensure uniqueness
        sku += ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        
        return sku

    # Function to update the SKU based on current inputs
    def update_design_sku():
        """Update the design SKU based on current form inputs"""
        if 'design_name' in st.session_state and st.session_state.design_name:
            colors = st.session_state.selected_colors if 'selected_colors' in st.session_state else []
            sizes = st.session_state.selected_sizes if 'selected_sizes' in st.session_state else []
            marketplace_title = st.session_state.marketplace_title if 'marketplace_title' in st.session_state else ""
            
            # Generate the new SKU
            new_sku = generate_product_sku(
                st.session_state.design_name, 
                colors, 
                sizes, 
                marketplace_title
            )
            
            # Update the session state
            st.session_state.design_sku = new_sku
            return new_sku
        return ""

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
    print("Products DataFrame:", products_df)

    # Initialize session state for selected product
    if 'selected_product_id' not in st.session_state:
        st.session_state.selected_product_id = None
    if 'selected_product_data' not in st.session_state:
        st.session_state.selected_product_data = None

    # Define the available options for sizes and colors
    AVAILABLE_SIZES = ["Small", "Medium", "Large", "XL", "2XL"]
    AVAILABLE_COLORS = ["Black", "Navy", "Grey", "White", "Red", "Blue", "Green", "Yellow", "Purple"]

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
            if (product_data):
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

    # Initialize session state for tracking design image
    if 'design_image_data' not in st.session_state:
        st.session_state.design_image_data = None

    def on_file_upload():
        """Callback for when a file is uploaded"""
        if st.session_state.design_image is not None:
            st.session_state.design_image_data = st.session_state.design_image

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
            default_design_sku = ""  # Will be auto-generated
            default_sizes = []
            default_colors = []
            
            # Use product data if available
            if st.session_state.selected_product_data:
                product = st.session_state.selected_product_data
                default_design_name = product['product_name']
                default_marketplace_title = product['marketplace_title'] or ""
                default_design_sku = product['item_sku'] or ""
                
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
            design_name = st.text_input("Design Name", value=default_design_name, placeholder="Value", key="design_name", 
                                    on_change=update_design_sku)
            
            marketplace_title = st.text_input("Marketplace Title (80 character limit)", 
                                            value=default_marketplace_title, 
                                            placeholder="Value", 
                                            key="marketplace_title",
                                            on_change=update_design_sku)
            
            # Generate initial SKU if needed
            if not default_design_sku and default_design_name:
                default_design_sku = generate_product_sku(
                    default_design_name, 
                    default_colors, 
                    default_sizes, 
                    default_marketplace_title
                )
                st.session_state.design_sku = default_design_sku
            elif not 'design_sku' in st.session_state or not st.session_state.design_sku:
                st.session_state.design_sku = default_design_sku
            
            # Display the generated or loaded SKU
            design_sku = st.text_input("Design SKU", value=st.session_state.design_sku, disabled=True, key="design_sku_display")

            # Multi-select for sizes and colors - using our defined constants
            sizes = st.multiselect("Select Sizes", AVAILABLE_SIZES, default=default_sizes, key="selected_sizes", 
                                on_change=update_design_sku)
            
            # Colors multiselect with defaults
            colors = st.multiselect("Select Colours", AVAILABLE_COLORS, default=default_colors, key="selected_colors", 
                                on_change=update_design_sku)

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

            # Modified file uploader with on_change callback to persist the uploaded file
            design_image = st.file_uploader("Design Image", type=["png", "jpg", "jpeg"], 
                                        key="design_image", 
                                        on_change=on_file_upload)
            
            # Use the persisted image if available but not currently selected
            if design_image is None and st.session_state.design_image_data is not None:
                design_image = st.session_state.design_image_data

            # Show mockup ID and smart object UUID if available
            if st.session_state.selected_product_data and st.session_state.selected_product_data.get('mockup_id'):
                st.info(f"Using Mockup ID: {st.session_state.selected_product_data['mockup_id']}")
            
            if st.session_state.selected_product_data and st.session_state.selected_product_data.get('smart_object_uuid'):
                st.info(f"Using Smart Object UUID: {st.session_state.selected_product_data['smart_object_uuid']}")

            # Generate Mockups button
            if st.button("Generate Mockups"):
                if not design_image:
                    st.error("Please upload a design image to generate mockups.")
                    return
                    
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
                    st.session_state.original_design_url = image_url
                    
                    # Success! Show the uploaded image URL
                    st.success("✅ Image uploaded to S3")
                
                # Step 2: Now that we have a valid image URL from S3, generate mockups for all colors
                with st.spinner("Generating mockups with the uploaded image..."):
                    # Convert color names to hex format
                    color_hex_list = [color_name_to_hex(color) for color in selected_colors]                
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
                        
                        # Make sure we have the latest SKU
                        current_sku = update_design_sku()
                        
                        # Store the selected product details to save later
                        st.session_state.product_data_to_save = {
                            "design_name": design_name,
                            "marketplace_title": marketplace_title,
                            "design_sku": current_sku,
                            "sizes": sizes,
                            "colors": colors,
                            "original_design_url": image_url
                        }
                        
                        # Success! Show the generated mockups
                        st.success(f"✅ Generated {len(mockup_results)} mockups successfully!")
                    else:
                        st.error("Failed to generate any mockups. See error details above.")
                        st.session_state.mockup_results = None
                        
            # Add Save Product button that appears only after mockups are generated
            if st.session_state.mockup_results and hasattr(st.session_state, 'product_data_to_save'):
                if st.button("Save Product to Database", key="save_product_button"):
                    with st.spinner("Saving mockups to S3 and product to database..."):
                        # Make sure we have the latest SKU before saving
                        design_sku = st.session_state.product_data_to_save["design_sku"]
                        if not design_sku:
                            design_sku = update_design_sku()
                            st.session_state.product_data_to_save["design_sku"] = design_sku
                        
                        # Step 1: Save mockups to S3 more efficiently
                        mockup_s3_urls = {}
                        progress_bar = st.progress(0)
                        
                        # Import necessary libraries upfront
                        import tempfile
                        import os
                        import io
                        import boto3
                        from botocore.exceptions import ClientError
                        import concurrent.futures
                        
                        # Initialize S3 client once
                        s3_client = boto3.client('s3', 
                            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                            region_name=os.environ.get('AWS_REGION', 'us-east-1')
                        )
                        bucket_name = os.environ.get('AWS_BUCKET_NAME', 'streamlet')
                        region = os.environ.get('AWS_REGION', 'us-east-1')
                        
                        # Create a temp directory but log less information
                        temp_dir = tempfile.mkdtemp()
                        
                        # Process mockups with optimized logging
                        total_mockups = len(st.session_state.mockup_results)
                        completed = 0
                        
                        # Function to process a single mockup
                        def process_mockup(hex_color, mockup_url):
                            try:
                                # Download the mockup image with optimized parameters
                                response = requests.get(mockup_url, timeout=10)
                                if response.status_code == 200:
                                    # Get a color name for the filename
                                    color_name = hex_to_color_name(hex_color) or hex_color.lstrip('#')
                                    local_filename = f"mockup_{design_sku}_{color_name}.png"
                                    local_filepath = os.path.join(temp_dir, local_filename)
                                    
                                    # More efficient file writing
                                    with open(local_filepath, 'wb') as f:
                                        f.write(response.content)
                                    
                                    # Create the S3 object key
                                    s3_folder = "mockups"
                                    s3_key = f"{s3_folder}/{local_filename}"
                                    
                                    # Optimized S3 upload with better parameters
                                    s3_client.upload_file(
                                        local_filepath,
                                        bucket_name,
                                        s3_key,
                                        ExtraArgs={
                                            'ContentType': 'image/png',
                                            'StorageClass': 'STANDARD',  # Use standard storage class for faster uploads
                                        },
                                        Config=boto3.s3.transfer.TransferConfig(
                                            use_threads=True,
                                            max_concurrency=10,
                                            multipart_threshold=8388608,  # 8MB - Use smaller chunks for faster start
                                            multipart_chunksize=8388608,  # 8MB
                                        )
                                    )
                                    
                                    # Generate the URL for the uploaded file
                                    s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
                                    return hex_color, s3_url, None
                                else:
                                    return hex_color, None, f"Failed to download mockup (Status: {response.status_code})"
                            except Exception as e:
                                return hex_color, None, str(e)
                        
                        # Process each mockup sequentially but with optimized code
                        items = list(st.session_state.mockup_results.items())
                        for i, (hex_color, mockup_url) in enumerate(items):
                            hex_color, s3_url, error = process_mockup(hex_color, mockup_url)
                            
                            if s3_url:
                                mockup_s3_urls[hex_color] = s3_url
                            elif error:
                                st.warning(f"Error processing mockup: {error}")
                            
                            # Update progress with less UI overhead
                            completed += 1
                            progress_bar.progress(completed / total_mockups)
                        
                        # Clean up temp directory
                        import shutil
                        try:
                            shutil.rmtree(temp_dir)
                        except Exception:
                            pass  # Ignore cleanup errors to avoid overhead
                        
                        # Step 2: Save product data to database with S3 mockup URLs
                        if mockup_s3_urls:
                            try:
                                # Get product data
                                product_data = st.session_state.product_data_to_save
                                
                                # Get parent SKU if available
                                parent_sku = ""
                                if st.session_state.selected_product_id:
                                    parent_product = db.get_product(st.session_state.selected_product_id)
                                    if parent_product and 'item_sku' in parent_product:
                                        parent_sku = parent_product['item_sku']
                                
                                # Create product data dictionary with minimal processing
                                product_dict = {
                                    "product_name": product_data["design_name"],
                                    "marketplace_title": product_data["marketplace_title"],
                                    "item_sku": product_data["design_sku"],  # Use design_sku as item_sku
                                    "parent_sku": parent_sku,  # Set parent_sku from selected product if available
                                    "size": json.dumps(product_data["sizes"]),
                                    "color": json.dumps([color_name_to_hex(color) for color in product_data["colors"]]),
                                    "original_design_url": product_data["original_design_url"],
                                    "mockup_urls": json.dumps(mockup_s3_urls)
                                }
                                
                                # Add parent_product_id if editing an existing product
                                if st.session_state.selected_product_id:
                                    product_dict["parent_product_id"] = st.session_state.selected_product_id
                                
                                # Create the product in a single database call
                                new_id = db.create_generated_product(product_dict)
                                success = new_id is not None
                                message = "created" if success else "create"
                                
                                if success:
                                    st.success(f"Product successfully {message} in database!")
                                    st.session_state.product_data_to_save = None
                                else:
                                    st.error(f"Failed to {message} product in database")
                            except Exception as e:
                                st.error(f"Error saving product to database: {str(e)}")
                        else:
                            st.error("No mockups were successfully saved to S3. Cannot save product.")

        # Initialize the mockup color tracking
        if 'original_mockup_colors' not in st.session_state:
            st.session_state.original_mockup_colors = {}
        if 'panel_color_mapping' not in st.session_state:
            st.session_state.panel_color_mapping = {}

        with right_col:
            # Preview by color
            st.write("### Preview by Colour")
            
            # Check if we have mockups to display
            if st.session_state.mockup_results:
                # Get all generated mockups
                available_mockup_colors = list(st.session_state.mockup_results.keys())
                
                # Convert hex colors to color names for better display
                mockup_color_names = []
                for hex_color in available_mockup_colors:
                    color_name = hex_to_color_name(hex_color.lstrip('#'))
                    mockup_color_names.append(color_name or "Unknown")
                
                # Store the original mockup colors if not already tracked
                if not st.session_state.original_mockup_colors:
                    for idx, hex_color in enumerate(available_mockup_colors):
                        st.session_state.original_mockup_colors[idx] = hex_color
                        # Map panel index to the original hex color
                        st.session_state.panel_color_mapping[idx] = hex_color
                            
                # Check if we need to generate a new mockup based on color selection
                if st.session_state.generate_for_panel is not None and st.session_state.generate_color is not None:
                    panel_idx = st.session_state.generate_for_panel
                    color_name = st.session_state.generate_color
                    hex_selected = color_name_to_hex(color_name)
                    
                    with st.spinner(f"Generating mockup for {color_name}..."):
                        # Only generate if we don't already have this color
                        if hex_selected not in st.session_state.mockup_results:
                            if generate_on_demand_mockup(color_name):
                                # Update the panel color mapping
                                st.session_state.panel_color_mapping[panel_idx] = hex_selected
                        
                        # Clear the flag after generation (whether successful or not)
                        st.session_state.generate_for_panel = None
                        st.session_state.generate_color = None
                        st.rerun()
                        
                # Determine the number of columns based on number of mockups
                if len(available_mockup_colors) <= 2:
                    num_cols = 2
                elif len(available_mockup_colors) <= 4:
                    num_cols = 3
                else:
                    num_cols = 4
                    
                # Create enough rows to hold all mockups
                for i in range(0, len(st.session_state.original_mockup_colors), num_cols):
                    # Create columns for this row of mockups
                    row_cols = st.columns(num_cols)
                    
                    # Fill the row with mockups based on original panel structure
                    for col_idx in range(num_cols):
                        mockup_idx = i + col_idx
                        if mockup_idx in st.session_state.original_mockup_colors:
                            # Get current color for this panel from mapping
                            current_hex_color = st.session_state.panel_color_mapping.get(mockup_idx)
                            original_hex_color = st.session_state.original_mockup_colors.get(mockup_idx)
                            
                            # Get color name for display
                            if current_hex_color and current_hex_color in st.session_state.mockup_results:
                                color_name = hex_to_color_name(current_hex_color.lstrip('#')) or "Unknown"
                            else:
                                color_name = hex_to_color_name(original_hex_color.lstrip('#')) or "Unknown"
                            
                            with row_cols[col_idx]:
                                # Create unique key for this preview panel
                                preview_key = f"preview_{mockup_idx}_color"
                                
                                # Initialize default selected color in mockup_panel_colors
                                if mockup_idx not in st.session_state.mockup_panel_colors:
                                    st.session_state.mockup_panel_colors[mockup_idx] = color_name if color_name in AVAILABLE_COLORS else AVAILABLE_COLORS[0]
                                
                                # Find index of current color or default to first color
                                default_index = 0
                                if st.session_state.mockup_panel_colors[mockup_idx] in AVAILABLE_COLORS:
                                    default_index = AVAILABLE_COLORS.index(st.session_state.mockup_panel_colors[mockup_idx])
                                
                                # Color selection dropdown with on_change callback
                                selected_color = st.selectbox(
                                    f"Mockup {mockup_idx + 1}", 
                                    AVAILABLE_COLORS,
                                    index=default_index,
                                    key=preview_key,
                                    on_change=on_mockup_color_change,
                                    args=(mockup_idx,)
                                )
                                
                                # Get hex value for selected color
                                hex_selected = color_name_to_hex(selected_color)
                                
                                # Display the mockup for the selected color if available
                                if hex_selected in st.session_state.mockup_results:
                                    st.image(
                                        st.session_state.mockup_results[hex_selected],
                                        caption=f"{selected_color} ({hex_selected})",
                                        use_container_width=True
                                    )
                                else:
                                    # If we don't have this color yet, show generate button
                                    st.write(f"No mockup available for {selected_color}")
                                    if st.button("Generate This Color", key=f"gen_mockup_{mockup_idx}"):
                                        # Set flags for generation on next render cycle
                                        st.session_state.generate_for_panel = mockup_idx
                                        st.session_state.generate_color = selected_color
                                        st.rerun()
            else:
                # Case when no mockups have been generated yet
                st.info("Generate mockups to see previews here")
                # Create 3 columns for color selection dropdowns
                col1, col2, col3 = st.columns(3)
                
                # Only show colors that were selected for the product
                available_colors = colors if colors else AVAILABLE_COLORS
                
                with col1:
                    color1 = st.selectbox(
                        "Select Color 1", 
                        available_colors,
                        key="preview1_color"
                    )
                    
                    # Show placeholder if no mockup available yet
                    if design_image:
                        st.image(design_image, width=150, caption=f"{color1} (Preview Only)")
                        if st.session_state.uploaded_image_url:
                            if st.button("Generate Mockup", key="gen_mockup1"):
                                if generate_on_demand_mockup(color1):
                                 st.rerun()
                    else:
                        st.image("https://via.placeholder.com/150", width=150, caption=color1)
                
                with col2:
                    color2 = st.selectbox(
                        "Select Color 2", 
                        available_colors,
                        key="preview2_color"
                    )
                    
                    # Show placeholder if no mockup available yet
                    if design_image:
                        st.image(design_image, width=150, caption=f"{color2} (Preview Only)")
                        if st.session_state.uploaded_image_url:
                            if st.button("Generate Mockup", key="gen_mockup2"):
                                if generate_on_demand_mockup(color2):
                                 st.rerun()
                    else:
                        st.image("https://via.placeholder.com/150", width=150, caption=color2)
                
                with col3:
                    color3 = st.selectbox(
                        "Select Color 3", 
                        available_colors,
                        key="preview3_color"
                    )
                    
                    # Show placeholder if no mockup available yet
                    if design_image:
                        st.image(design_image, width=150, caption=f"{color3} (Preview Only)")
                        if st.session_state.uploaded_image_url:
                            if st.button("Generate Mockup", key="gen_mockup3"):
                                if generate_on_demand_mockup(color3):
                                 st.rerun()
                    else:
                        st.image("https://via.placeholder.com/150", width=150, caption=color3)

    # Initialize session state for tracking product data to save
    if 'product_data_to_save' not in st.session_state:
        st.session_state.product_data_to_save = None
    if 'original_design_url' not in st.session_state:
        st.session_state.original_design_url = None

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

    # Initialize specific session state variables for tracking mockup panel selections
    if 'mockup_panel_colors' not in st.session_state:
        st.session_state.mockup_panel_colors = {}
    if 'generate_for_panel' not in st.session_state:
        st.session_state.generate_for_panel = None
    if 'generate_color' not in st.session_state:
        st.session_state.generate_color = None

    # Add a function to handle color selection changes
    def on_mockup_color_change(mockup_idx):
        """Handle color change in the mockup preview panel"""
        if mockup_idx not in st.session_state.panel_color_mapping:
            return
            
        preview_key = f"preview_{mockup_idx}_color"
        selected_color = st.session_state[preview_key]
        hex_selected = color_name_to_hex(selected_color)
        
        # Store the selected color in our tracking dictionary
        st.session_state.mockup_panel_colors[mockup_idx] = selected_color
        
        # If we don't have this color yet, generate it
        if hex_selected not in st.session_state.mockup_results:
            # Set only once to avoid double triggering
            if st.session_state.generate_for_panel is None:
                st.session_state.generate_for_panel = mockup_idx
                st.session_state.generate_color = selected_color
        else:
            # If we already have this color, update the panel mapping directly
            st.session_state.panel_color_mapping[mockup_idx] = hex_selected

    # Call the function to render the page
    generate_product_page()