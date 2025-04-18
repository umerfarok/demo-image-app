import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv
from utils.s3_storage import upload_mockup_to_s3
import time

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

def get_mockups():
    """
    Fetch available mockups from the Dynamic Mockups API
    
    Returns:
        list: List of mockup data if successful, empty list otherwise
    """
    try:
        response = requests.get(
            'https://app.dynamicmockups.com/api/v1/mockups',
            headers={
                'Accept': 'application/json',
                'x-api-key': os.getenv('DYNAMIC_MOCKUPS_API_KEY'),
            },
        )
        
        if response.status_code != 200:
            st.error(f"API returned error status: {response.status_code}")
            st.error(f"Response content: {response.text}")
            return []
            
        result = response.json()
        
        if 'data' in result and isinstance(result['data'], list):
            return result['data']
        else:
            st.error("Invalid API response format")
            return []
            
    except Exception as e:
        st.error(f"Error fetching mockups: {e}")
        return []

def generate_mockup(image_url, color, mockup_id=None, smart_object_uuid=None):
    """
    Generate a mockup using the Dynamic Mockups API
    
    Args:
        image_url (str): URL of the image to use for the mockup
        color (str): Hex color code for the mockup
        mockup_id (str, optional): ID of the mockup to use
        smart_object_uuid (str, optional): UUID of the smart object to use
        
    Returns:
        dict: Mockup data if successful, None otherwise
    """
    # Default mockup and smart object UUIDs if not provided
    MOCKUP_UUID = mockup_id or "9ffb48c2-264f-42b9-ab86-858c410422cc"
    SMART_OBJECT_UUID = smart_object_uuid or "cc864498-b8d1-495a-9968-45937edf42b3"
    
    try:
        # Create request data
        request_data = {
            "mockup_uuid": MOCKUP_UUID,
            "smart_objects": [
                {
                    "uuid": SMART_OBJECT_UUID,
                    "color": color,
                    "asset": {
                        "url": image_url
                    }
                }
            ],
            "format": "png",
            "width": 1500,
            "transparent_background": True
        }
        
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
            return None
            
        result = response.json()
        
        # Get the rendered image URL from the response
        if 'data' in result and 'export_path' in result['data']:
            return result['data']
        else:
            st.error("Expected 'data.export_path' in API response but it was not found")
            return None
            
    except Exception as e:
        st.error(f"Error generating mockup: {e}")
        return None

def batch_generate_mockups(image_url, colors, mockup_id=None, smart_object_uuid=None, delay=1):
    """
    Generate multiple mockups in sequence using the Dynamic Mockups API
    
    Args:
        image_url (str): URL of the image to use for all mockups
        colors (list): List of hex color codes to generate mockups for
        mockup_id (str, optional): ID of the mockup to use
        smart_object_uuid (str, optional): UUID of the smart object to use
        delay (int, optional): Delay between API requests in seconds
        
    Returns:
        list: List of mockup data if successful, empty list otherwise
    """
    results = []
    
    for i, color in enumerate(colors):
        # Generate the mockup for this color
        mockup_data = generate_mockup_api_call(
            image_url, 
            color, 
            mockup_id, 
            smart_object_uuid
        )
        
        if mockup_data:
            results.append(mockup_data)
        
        # Add a delay between requests to avoid rate limiting, except for the last color
        if i < len(colors) - 1:
            time.sleep(delay)
    
    return results

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

def generate_mockup_for_all_templates(image_url, colors, mockup_ids, smart_object_uuids):
    """
    Generate mockups for multiple templates
    
    Args:
        image_url (str): URL of the image to use
        colors (list): List of hex color codes
        mockup_ids (list): List of mockup IDs
        smart_object_uuids (list): List of smart object UUIDs
        
    Returns:
        dict: Dictionary with results for each mockup ID
    """
    results = {}
    
    # Ensure smart_object_uuids is same length as mockup_ids
    if len(smart_object_uuids) < len(mockup_ids):
        smart_object_uuids.extend([None] * (len(mockup_ids) - len(smart_object_uuids)))
    
    # Generate mockups for each template and color combination
    for i, (mockup_id, smart_object_uuid) in enumerate(zip(mockup_ids, smart_object_uuids)):
        template_results = []
        
        for color in colors:
            # Generate mockup for this specific template and color
            mockup_data = generate_mockup_api_call(
                image_url=image_url,
                color=color,
                mockup_id=mockup_id,
                smart_object_uuid=smart_object_uuid
            )
            
            if mockup_data:
                template_results.append(mockup_data)
                
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Store results for this template
        if template_results:
            results[mockup_id] = {
                'mockup_id': mockup_id,
                'smart_object_uuid': smart_object_uuid,
                'results': template_results
            }
    
    return results

def generate_mockup_api_call(image_url, color, mockup_id, smart_object_uuid):
    """
    Make a single API call to generate a mockup
    
    Args:
        image_url (str): URL of the image to use
        color (str): Hex color code
        mockup_id (str): Mockup ID to use
        smart_object_uuid (str): Smart object UUID to use
        
    Returns:
        dict: Mockup data with rendered URL or None if failed
    """
    # Use provided IDs or fall back to defaults
    MOCKUP_UUID = mockup_id or "db90556b-96a3-483c-ba88-557393b992a1"
    SMART_OBJECT_UUID = smart_object_uuid or "fb677f24-3dce-4d53-b024-26ea52ea43c9"
    
    try:
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
        
        # Log the request data for debugging
        print(f"Request data for mockup {MOCKUP_UUID}, smart object {SMART_OBJECT_UUID}:")
        print(json.dumps(request_data, indent=2))
        
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
            print(f"API returned error status: {response.status_code}")
            print(f"Response content: {response.text}")
            return None
            
        result = response.json()
        
        # Get the rendered image URL from the response
        if 'data' in result and 'export_path' in result['data']:
            mockup_data = {
                'rendered_image_url': result['data']['export_path'],
                'color': color
            }
            return mockup_data
        else:
            print("Expected 'data.export_path' in API response but it was not found")
            return None
            
    except Exception as e:
        print(f"Error generating mockup: {e}")
        return None
