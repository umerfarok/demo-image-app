import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv
from utils.s3_storage import upload_mockup_to_s3

# Load environment variables
load_dotenv()

# DynamicMockups API configuration
API_KEY = os.getenv('DYNAMIC_MOCKUPS_API_KEY')
API_BASE_URL = "https://app.dynamicmockups.com/api/v1"

def get_mockup_collections():
    """
    Get list of available mockup collections
    
    Returns:
        list: List of collections or empty list if error occurs
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/collections",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        
        if response.status_code == 200:
            print(f"API response: {response.json()}")
            return response.json().get('collections', [])
        else:
            print(f"Failed to fetch collections: {response.status_code}")
            st.error(f"Failed to fetch mockup collections: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching mockup collections: {e}")
        st.error(f"Error fetching mockup collections: {e}")
        return []

def get_mockups(collection_id=None, category=None, limit=100):
    try:
        params = {"limit": limit}
        if collection_id:
            params["collection"] = collection_id
        if category:
            params["category"] = category
            
        response = requests.get(
            f"{API_BASE_URL}/mockups",
            headers={"x-api-key": f"{API_KEY}"},
            # params=params
        )
        
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Failed to fetch mockups: {response.status_code}")
            st.error(f"Failed to fetch mockups: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching mockups: {e}")
        st.error(f"Error fetching mockups: {e}")
        return []

def generate_mockup_with_color(image_url, mockup_id, color_hex=None, output_format="jpg"):
    """
    Generate a mockup with the given image and color
    
    Args:
        image_url: URL of the design image to apply
        mockup_id: ID of the mockup template
        color_hex: Optional hex color code for customization (if supported by the mockup)
        output_format: Output format (jpg or png)
        
    Returns:
        str: S3 URL of the generated mockup or None if error occurs
    """
    try:
        # Prepare the payload
        payload = {
            "template_id": mockup_id,
            "output_format": output_format,
            "layers": [
                {
                    "name": "design",  # This might need adjustment based on the template
                    "image_url": image_url
                }
            ]
        }
        
        # Add color customization if provided
        if color_hex:
            # Remove # if present
            color_hex = color_hex.lstrip('#')
            payload["colors"] = {
                "primary": color_hex  # This might need adjustment based on the template
            }
        
        st.write(f"Sending API request to generate mockup with template: {mockup_id}")
        
        # Call the render API
        response = requests.post(
            f"{API_BASE_URL}/render",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            # Get the mockup URL from the response
            mockup_url = response.json().get('url')
            
            if mockup_url:
                st.write(f"Successfully generated mockup from API: {mockup_url[:50]}...")
                
                # Upload mockup to S3
                s3_url = upload_mockup_to_s3(mockup_url, is_url=True)
                
                if not s3_url:
                    st.error("Failed to upload mockup to S3.")
                
                return s3_url
            else:
                st.error("API returned success but no mockup URL found in response")
                return None
        else:
            st.error(f"Failed to generate mockup: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error generating mockup: {e}")
        return None

def get_mockup_details(mockup_id):
    """
    Get details for a specific mockup template
    
    Args:
        mockup_id: ID of the mockup template
        
    Returns:
        dict: Mockup details or None if error occurs
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/mockups/{mockup_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        
        if response.status_code == 200:
            return response.json().get('mockup')
        else:
            st.error(f"Failed to fetch mockup details: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching mockup details: {e}")
        return None

def upload_psd_template(psd_file_path, name, category=None, tags=None):
    """
    Upload a custom PSD template
    
    Args:
        psd_file_path: Path to the PSD file
        name: Name for the custom template
        category: Optional category
        tags: Optional list of tags
        
    Returns:
        dict: Upload response or None if error occurs
    """
    try:
        # Prepare the metadata
        metadata = {
            "name": name
        }
        
        if category:
            metadata["category"] = category
            
        if tags:
            metadata["tags"] = tags
            
        # Open file for upload
        with open(psd_file_path, 'rb') as psd_file:
            files = {
                'file': (os.path.basename(psd_file_path), psd_file, 'application/octet-stream'),
                'metadata': (None, json.dumps(metadata), 'application/json')
            }
            
            response = requests.post(
                f"{API_BASE_URL}/psd/upload",
                headers={"Authorization": f"Bearer {API_KEY}"},
                files=files
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to upload PSD template: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        st.error(f"Error uploading PSD template: {e}")
        return None
