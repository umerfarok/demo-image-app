import streamlit as st
import pandas as pd
import os
# from utils.auth import check_password
from utils.database import get_database_connection
from PIL import Image
import io
import requests
import json  # Add import for JSON handling
from utils.api import is_s3_url
from utils.s3_storage import get_image_from_s3_url

# Verify authentication
# if not check_password():
#     st.stop()

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
if 'view_product_type' not in st.session_state:
    st.session_state.view_product_type = None

# Initialize pagination state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'items_per_page' not in st.session_state:
    st.session_state.items_per_page = 5

# Initialize product type filter
if 'product_type_filter' not in st.session_state:
    st.session_state.product_type_filter = "All"

# Get all products from database
products_df = db.get_all_products()
generated_products_df = db.get_all_generated_products()

# Add a type column to distinguish between regular and generated products
if not products_df.empty:
    products_df['product_type'] = 'Regular'

if not generated_products_df.empty:
    generated_products_df['product_type'] = 'Generated'
    # Rename design_sku to item_sku for consistency in display
    if 'design_sku' in generated_products_df.columns:
        generated_products_df = generated_products_df.rename(columns={'design_sku': 'item_sku'})

# Handle delete confirmation modal
if st.session_state.confirm_delete:
    product_id = st.session_state.product_to_delete
    product_type = st.session_state.product_type
    
    if product_type == "Regular":
        product = db.get_product(product_id)
        product_name = product['product_name']
    else:  # Generated
        product = db.get_generated_product(product_id)
        product_name = product['product_name']
    
    # Create modal-like dialog with warning style
    st.warning("⚠️ Delete Confirmation")
    st.write(f"Are you sure you want to delete **{product_name}**?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete", type="primary"):
            success = False
            if product_type == "Regular":
                success = db.delete_product(product_id)
            else:  # Add a delete_generated_product method if needed
                # Assume this method exists or needs to be created
                success = db.delete_product(product_id)  # Replace with appropriate method
            
            if success:
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
    product_type = st.session_state.view_product_type
    
    if product_type == "Regular":
        product = db.get_product(product_id)
    else:  # Generated
        product = db.get_generated_product(product_id)
    
    # Back button
    if st.button("← Back to Product List"):
        st.session_state.view_product_id = None
        st.session_state.view_product_type = None
        st.experimental_rerun()
    
    # Display product details with improved layout
    st.subheader(f"Product Details: {product['product_name']} ({product_type} Product)")
    
    # Replace the column layout with a single flow
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
        "Color": color_value
    }
    
    # Handle price for regular products
    if product_type == "Regular" and 'price' in product:
        product_details["Price"] = f"${product['price']}"
        
    # Handle category
    if 'category' in product and product:
        product_details["Category"] = product['category']
        
    # Add SKU information (different field names for different product types)
    if product_type == "Regular" and 'item_sku' in product:
        product_details["SKU"] = product['item_sku']
    elif product_type == "Generated" and 'design_sku' in product:
        product_details["Design SKU"] = product['design_sku']
        
    # Add generated product specific fields
    if product_type == "Generated":
        if 'is_published' in product:
            product_details["Published"] = "Yes" if product['is_published'] else "No"
            
    # Add created_at if available
    if 'created_at' in product and product['created_at']:
        product_details["Created at"] = product['created_at']
        
    # Convert dictionary to DataFrame for table display
    details_df = pd.DataFrame(product_details.items(), columns=['Attribute', 'Value'])
    st.table(details_df)
    
    # Add separator before images
    st.markdown("---")
    st.subheader("Product Images")
    
    # Display product image if available
    if product_type == "Generated" and 'mockup_urls' in product and product['mockup_urls']:
        image_field = 'mockup_urls'
        image_url = product[image_field]
        
        try:
            import json
            # Parse mockup_urls JSON
            if isinstance(image_url, str) and (image_url.startswith('[') or image_url.startswith('{')):
                mockup_data = json.loads(image_url)
                # Extract all URLs from the mockup data
                if isinstance(mockup_data, dict) and len(mockup_data) > 0:
                    # Display all mockups for different colors
                    st.write("Available mockups:")
                    for color_code, mockup_url in mockup_data.items():
                        color_name = color_code.replace("#", "")  # Remove # from hex code for display
                        st.image(mockup_url, caption=f"Mockup - {color_name}", width=300)
                elif isinstance(mockup_data, list) and len(mockup_data) > 0:
                    for i, url in enumerate(mockup_data):
                        st.image(url, caption=f"Mockup {i+1}", width=300)
            else:
                st.image(image_url, caption=f"Mockup for {product['product_name']}", width=300)
        except Exception as e:
            st.error(f"Error parsing mockup URL: {e}")
            st.markdown("📷 *Mockup image could not be loaded*")
    else:
        # Use default image fields and logic for regular products
        image_field = 'image_url' if product_type == "Regular" else 'original_design_url'
        if product[image_field]:
            st.image(product[image_field], caption=f"Image for {product['product_name']}", width=300)
        else:
            st.markdown("📷 *No image available*")

else:
    # Add search and filter functionality - Only shown when not viewing a single product
    st.subheader("Search & Filter")

    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("Search by name or SKU", "")

    with col2:
        # Create combined category list from both regular and generated products
        categories = []
        if not products_df.empty and 'category' in products_df.columns:
            categories = products_df['category'].dropna().unique().tolist()
        categories = ["All"] + categories
        category_filter = st.selectbox("Filter by category", categories)

    with col3:
        # Add product type filter
        product_type_options = ["All", "Regular", "Generated"]
        product_type_filter = st.selectbox("Product type", product_type_options)
        st.session_state.product_type_filter = product_type_filter

    # Add CSV export button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Generate CSV File for All Product"):
            # Combine DataFrames based on filter selection
            if st.session_state.product_type_filter == "All":
                filtered_df = pd.concat([products_df, generated_products_df], ignore_index=True)
            elif st.session_state.product_type_filter == "Regular":
                filtered_df = products_df.copy()
            else:  # Generated
                filtered_df = generated_products_df.copy()

            # Apply additional filters
            if not filtered_df.empty:
                if 'price' in filtered_df.columns:
                    filtered_df['price'] = pd.to_numeric(filtered_df['price'], errors='coerce').fillna(0.0)
                if 'quantity' in filtered_df.columns:
                    filtered_df['quantity'] = pd.to_numeric(filtered_df['quantity'], errors='coerce').fillna(0).astype(int)
                
                # Format size data - clean up JSON arrays
                if 'size' in filtered_df.columns:
                    def clean_size_format(size_val):
                        if pd.isna(size_val) or size_val == '':
                            return ''
                        try:
                            if isinstance(size_val, str):
                                if size_val.startswith('[') or size_val.startswith('{'):
                                    # Parse JSON
                                    size_data = json.loads(size_val)
                                    if isinstance(size_data, list):
                                        # Handle list of dictionaries with 'name' field
                                        if all(isinstance(item, dict) and 'name' in item for item in size_data):
                                            return ','.join([item['name'] for item in size_data])
                                        # Handle list of strings
                                        return ','.join(str(s).strip('"\'') for s in size_data)
                                    return str(size_data)
                            return str(size_val)
                        except:
                            return str(size_val)
                    
                    filtered_df['size'] = filtered_df['size'].apply(clean_size_format)
                
                # Format color data - clean up JSON arrays
                for color_field in ['color', 'colour']:
                    if color_field in filtered_df.columns:
                        def clean_color_format(color_val):
                            if pd.isna(color_val) or color_val == '':
                                return ''
                            try:
                                if isinstance(color_val, str):
                                    if color_val.startswith('[') or color_val.startswith('{'):
                                        # Parse JSON
                                        color_data = json.loads(color_val)
                                        if isinstance(color_data, list):
                                            # Remove quotes and join with commas
                                            return ','.join(str(c).strip('"\'') for c in color_data)
                                        return str(color_data)
                                return str(color_val)
                            except:
                                return str(color_val)
                        
                        filtered_df[color_field] = filtered_df[color_field].apply(clean_color_format)

            # Store the filtered DataFrame in session state for export
            st.session_state.export_csv_data = filtered_df.to_csv(index=False)

            st.success("CSV data prepared! Please proceed to the Export page to download the file.")

    # Combine DataFrames based on filter selection
    if product_type_filter == "All":
        # Combine both dataframes, ensuring they have compatible columns
        filtered_df = pd.concat([products_df, generated_products_df], ignore_index=True)
    elif product_type_filter == "Regular":
        filtered_df = products_df.copy()
    else:  # Generated
        filtered_df = generated_products_df.copy()

    # Apply additional filters
    if not filtered_df.empty:
        # Ensure numeric columns have proper data types for regular products
        if 'price' in filtered_df.columns:
            # Convert price to float with error handling
            filtered_df['price'] = pd.to_numeric(filtered_df['price'], errors='coerce').fillna(0.0)
        
        if 'quantity' in filtered_df.columns:
            # Convert quantity to integer with error handling
            filtered_df['quantity'] = pd.to_numeric(filtered_df['quantity'], errors='coerce').fillna(0).astype(int)

    # Search filter
    if search_term:
        # Ensure search works regardless of which product type
        search_columns = ['product_name', 'item_sku']
        
        # Build search mask dynamically based on available columns
        search_mask = pd.Series(False, index=filtered_df.index)
        for col in search_columns:
            if col in filtered_df.columns:
                search_mask |= filtered_df[col].str.contains(search_term, case=False, na=False)
        filtered_df = filtered_df[search_mask]

    # Category filter
    if category_filter != "All" and not filtered_df.empty and 'category' in filtered_df.columns:
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
        cols = st.columns([1, 3, 1, 1])
        with cols[0]:
            st.markdown("**Image**")
        with cols[1]:
            st.markdown("**Product Title**")
        with cols[2]:
            st.markdown("**Type**")
        with cols[3]:
            st.markdown("**Action**")
            
        # Add separator line
        st.markdown("<hr style='margin-top: 0; margin-bottom: 10px;'>", unsafe_allow_html=True)
        
        # Iterate through products and display in rows
        for idx, row in page_df.iterrows():
            product_id = row['id']
            product_name = row['product_name']
            product_type = row['product_type']
            
            # Print each product's data for debugging
            print(f"PRODUCT DATA: {product_type} - {product_id} - {product_name}")
            print(f"PRODUCT ROW DATA: {row}")
            
            cols = st.columns([1, 3, 1, 1])
            
            # Image column
            with cols[0]:
                # For generated products, use mockup_urls instead of original_design_url
                if product_type == 'Generated' and 'mockup_urls' in row and row['mockup_urls']:
                    image_field = 'mockup_urls'
                else:
                    # Use original_design_url as fallback for generated products with no mockups
                    image_field = 'mockup_urls' if product_type == 'Regular' else 'original_design_url'
                
                if image_field in row and row[image_field]:
                    image_url = row[image_field]
                    if image_field == 'mockup_urls':
                        try:
                            import json
                            if isinstance(image_url, str) and (image_url.startswith('[') or image_url.startswith('{')):
                                mockup_data = json.loads(image_url)
                                thumbnail_url = None
                                
                                if isinstance(mockup_data, dict) and len(mockup_data) > 0:
                                    # Just show the first color as thumbnail in the list
                                    first_key = list(mockup_data.keys())[0]
                                    thumbnail_url = mockup_data[first_key]
                                    # Show a count of additional mockups if there are multiple
                                    mockup_count = len(mockup_data)
                                    if mockup_count > 1:
                                        st.caption(f"+{mockup_count-1} more")
                                elif isinstance(mockup_data, list) and len(mockup_data) > 0:
                                    thumbnail_url = mockup_data[0]
                                    # Show a count of additional mockups if there are multiple
                                    if len(mockup_data) > 1:
                                        st.caption(f"+{len(mockup_data)-1} more")
                                
                                if thumbnail_url:
                                    st.image(thumbnail_url, width=70)
                                else:
                                    st.markdown("📷 *No mockup available*")
                        except Exception as e:
                            st.error(f"Error parsing mockup URL: {e}")
                            st.markdown("📷 *Invalid mockup data*")
                    # Ensure image_url is a valid string before displaying
                    elif image_url and isinstance(image_url, str):
                        st.image(image_url, width=70)
                    else:
                        st.markdown("📷 *Invalid or missing image URL*")
                else:
                    st.markdown("📷")
            
            # Product name column
            with cols[1]:
                st.write(product_name)
                
            # Product type column
            with cols[2]:
                st.write(product_type)
            
            # Action column
            with cols[3]:
                view_col, delete_col = st.columns(2)
                
                with view_col:
                    if st.button("View", key=f"view_{product_type}_{product_id}"):
                        st.session_state.view_product_id = product_id
                        st.session_state.view_product_type = product_type
                        st.experimental_rerun()
                
                with delete_col:
                    if st.button("Delete", key=f"delete_{product_type}_{product_id}"):
                        st.session_state.confirm_delete = True
                        st.session_state.product_to_delete = product_id
                        st.session_state.product_type = product_type
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
