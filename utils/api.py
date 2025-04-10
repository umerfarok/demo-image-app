import os
import requests
import streamlit as st
from PIL import Image
import uuid
import io
from config import API_KEY, API_URL, IMAGES_DIR, S3_CONFIG
from utils.s3_storage import upload_image_file_to_s3, upload_mockup_to_s3

def ensure_images_dir():
    """
    Ensure the images directory exists (as a backup only)
    """
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

def generate_mockup(image_path_or_url, template_id="t-shirt", is_s3_url=False):
    """
    Generate a mockup using DynamicMockups API and store in S3
    
    Args:
        image_path_or_url (str): Path to the image file or S3 URL
        template_id (str): Template ID to use
        is_s3_url (bool): Whether image_path_or_url is an S3 URL
        
    Returns:
        str: S3 URL to saved mockup image or None if failed
    """
    if not API_KEY:
        st.error("Missing API key. Please set DYNAMIC_MOCKUPS_API_KEY in .env file")
        return None
    
    try:
        url = f"{API_URL}/mockups"
        
        # If we have an S3 URL, we need to download the file first
        if is_s3_url:
            response = requests.get(image_path_or_url)
            if response.status_code != 200:
                st.error(f"Failed to download image from S3: {response.status_code}")
                return None
                
            # Create a temporary file-like object
            image_file = io.BytesIO(response.content)
            filename = f"temp_image_{uuid.uuid4()}.png"  # Name for the file in the request
        else:
            # Open the local file
            if not os.path.exists(image_path_or_url):
                st.error(f"Image file not found: {image_path_or_url}")
                return None
                
            image_file = open(image_path_or_url, 'rb')
            filename = os.path.basename(image_path_or_url)
            
        try:
            files = {
                'image': (filename, image_file, 'image/png')
            }
            
            data = {
                'template_id': template_id
            }
            
            headers = {
                'Authorization': f'Bearer {API_KEY}'
            }
            
            # Make the API request
            st.info("Sending request to DynamicMockups API...")
            response = requests.post(url, files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'mockup_url' in result:
                    # API returned a mockup URL
                    mockup_url = result['mockup_url']
                    
                    # Upload the mockup to our S3 bucket
                    st.info("Uploading mockup to S3...")
                    s3_url = upload_mockup_to_s3(mockup_url, True)
                    
                    if s3_url:
                        st.success("Mockup uploaded to S3 successfully")
                        return s3_url
                    else:
                        st.error("Failed to upload mockup to S3")
                        return None
            
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
        finally:
            # Close the file if it's a local file and not a BytesIO object
            if not is_s3_url and not isinstance(image_file, io.BytesIO):
                image_file.close()
            
    except Exception as e:
        st.error(f"Error calling API: {e}")
        return None

def save_uploaded_image(uploaded_file):
    """
    Save an uploaded image to S3
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        str: S3 URL to the saved image
    """
    if not uploaded_file:
        return None
        
    st.info("Uploading image to S3...")
    s3_url = upload_image_file_to_s3(uploaded_file)
    
    if s3_url:
        st.success("Image uploaded to S3 successfully")
        return s3_url
    
    # If S3 upload fails, log error and stop
    st.error("Failed to upload image to S3. Please check your S3 configuration.")
    return None

def is_s3_url(url_or_path):
    """Check if a string is an S3 URL"""
    if not url_or_path:
        return False
    
    return url_or_path.startswith('https://') and 's3.' in url_or_path

# Add validation function to verify image generation works
def verify_api_functionality():
    """
    Verify that the API functionality works correctly
    
    Returns:
        tuple: (success, message)
    """
    if not API_KEY:
        return False, "Missing API key. Please set DYNAMIC_MOCKUPS_API_KEY in .env file"
        
    # Test API access - make a simple call to verify API key works
    try:
        # Just test the authentication, don't make a full request
        headers = {
            'Authorization': f'Bearer {API_KEY}'
        }
        
        # Make a test request to the API (using templates endpoint which is lightweight)
        test_url = f"{API_URL}/templates"  # Most APIs have a templates or similar endpoint
        response = requests.get(test_url, headers=headers)
        
        if response.status_code == 200:
            return True, "API connection successful"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Error testing API connection: {e}"
