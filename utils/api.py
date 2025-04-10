import os
import requests
import streamlit as st
from PIL import Image
import uuid
from config import API_KEY, API_URL, IMAGES_DIR

def ensure_images_dir():
    """
    Ensure the images directory exists
    """
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

def generate_mockup(image_path, template_id="t-shirt"):
    """
    Generate a mockup using DynamicMockups API
    
    Args:
        image_path (str): Path to the image file
        template_id (str): Template ID to use
        
    Returns:
        str: Path to saved mockup image or None if failed
    """
    if not API_KEY:
        st.error("Missing API key. Please set DYNAMIC_MOCKUPS_API_KEY in .env file")
        return None
    
    # For demonstration, we'll simulate the API call to avoid actual API charges
    # In production, uncomment the API code and comment out the simulation code
    
    # Simulate API call (for demo without API charges)
    if os.path.exists(image_path):
        ensure_images_dir()
        
        # Generate unique filename for the mockup
        filename = f"mockup_{uuid.uuid4()}.png"
        output_path = os.path.join(IMAGES_DIR, filename)
        
        # For demo, we'll just modify the original image slightly (add text)
        try:
            # Open the original image
            img = Image.open(image_path)
            
            # Create a simulated mockup (just save a copy for demo)
            img.save(output_path)
            
            return output_path
        except Exception as e:
            st.error(f"Error generating mockup: {e}")
            return None
    
    # Real API implementation (commented out to avoid charges)
    """
    try:
        url = f"{API_URL}/mockups"
        
        with open(image_path, 'rb') as image_file:
            files = {
                'image': image_file
            }
            
            data = {
                'template_id': template_id
            }
            
            headers = {
                'Authorization': f'Bearer {API_KEY}'
            }
            
            response = requests.post(url, files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'mockup_url' in result:
                    # Download the mockup image
                    mockup_url = result['mockup_url']
                    mockup_response = requests.get(mockup_url)
                    
                    if mockup_response.status_code == 200:
                        ensure_images_dir()
                        
                        # Generate unique filename for the mockup
                        filename = f"mockup_{uuid.uuid4()}.png"
                        output_path = os.path.join(IMAGES_DIR, filename)
                        
                        # Save the mockup image
                        with open(output_path, 'wb') as f:
                            f.write(mockup_response.content)
                        
                        return output_path
            
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error calling API: {e}")
        return None
    """

def save_uploaded_image(uploaded_file):
    """
    Save an uploaded image to disk
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        str: Path to the saved image
    """
    ensure_images_dir()
    
    # Generate a unique filename
    file_extension = os.path.splitext(uploaded_file.name)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    save_path = os.path.join(IMAGES_DIR, filename)
    
    # Save the uploaded image
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return save_path
