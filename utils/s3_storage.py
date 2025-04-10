import boto3
import os
import uuid
import io
import streamlit as st
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import requests
from PIL import Image

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Folder structure in S3
ORIGINAL_FOLDER = 'original'
MOCKUP_FOLDER = 'mockups'

@st.cache_resource
def get_s3_client():
    """Get a cached S3 client connection"""
    try:
        if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
            st.error("AWS S3 credentials not fully configured. Check your .env file.")
            return None
            
        return boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    except Exception as e:
        st.error(f"Error connecting to AWS S3: {e}")
        return None

def upload_file_to_s3(file_content, folder, file_extension='.jpg', content_type='image/jpeg'):
    """
    Upload a file to S3 bucket
    
    Args:
        file_content: Binary content of the file
        folder: Folder within the bucket (original or mockups)
        file_extension: File extension including dot
        content_type: MIME type of the file
        
    Returns:
        str: S3 URL if successful, None otherwise
    """
    s3_client = get_s3_client()
    if not s3_client:
        st.error("Failed to connect to S3. Check your AWS credentials.")
        return None
        
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}{file_extension}"
        s3_key = f"{folder}/{filename}"
        
        # Upload to S3
        s3_client.put_object(
            Body=file_content,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            ContentType=content_type
        )
        
        # Generate the URL
        url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        st.error(f"Error uploading to S3: {e}")
        return None

def upload_image_file_to_s3(file, folder=ORIGINAL_FOLDER):
    """
    Upload a Streamlit uploaded image file to S3
    
    Args:
        file: Streamlit UploadedFile object
        folder: S3 folder to store in
        
    Returns:
        str: S3 URL if successful, None otherwise
    """
    if not file:
        return None
        
    try:
        # Get file details
        content = file.getvalue()
        file_extension = os.path.splitext(file.name)[1].lower()
        content_type = file.type
        
        # Upload to S3
        return upload_file_to_s3(content, folder, file_extension, content_type)
    except Exception as e:
        st.error(f"Error processing uploaded file: {e}")
        return None

def upload_mockup_to_s3(image_path_or_url, is_url=False):
    """
    Upload a mockup image to S3
    
    Args:
        image_path_or_url: Local path or URL of the mockup image
        is_url: Whether the image_path is actually a URL
        
    Returns:
        str: S3 URL if successful, None otherwise
    """
    try:
        if is_url:
            # Download from URL
            response = requests.get(image_path_or_url)
            if response.status_code != 200:
                st.error(f"Error downloading image: Status code {response.status_code}")
                return None
                
            content = response.content
            # Determine file extension based on content type
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            ext = '.jpg' if 'jpeg' in content_type else '.png'
        else:
            # Read local file
            if not os.path.exists(image_path_or_url):
                st.error(f"File not found: {image_path_or_url}")
                return None
                
            with open(image_path_or_url, 'rb') as f:
                content = f.read()
            
            ext = os.path.splitext(image_path_or_url)[1].lower()
            content_type = 'image/jpeg' if ext == '.jpg' or ext == '.jpeg' else 'image/png'
        
        # Upload to S3
        return upload_file_to_s3(content, MOCKUP_FOLDER, ext, content_type)
    except Exception as e:
        st.error(f"Error uploading mockup to S3: {e}")
        return None

def get_image_from_s3_url(s3_url):
    """
    Display an image from S3 URL in Streamlit
    
    Args:
        s3_url: S3 URL of the image
        
    Returns:
        Image object if successful, None otherwise
    """
    if not s3_url:
        return None
        
    try:
        response = requests.get(s3_url)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            st.error(f"Error fetching image: Status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error processing image from S3: {e}")
        return None

def delete_image_from_s3(s3_url):
    """
    Delete an image from S3 using its URL
    
    Args:
        s3_url: S3 URL of the image to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not s3_url:
        return False
        
    s3_client = get_s3_client()
    if not s3_client:
        return False
        
    try:
        # Extract key from URL
        # URL format: https://bucket-name.s3.region.amazonaws.com/key
        parts = s3_url.replace('https://', '').split('/')
        if len(parts) < 2:
            st.error(f"Invalid S3 URL format: {s3_url}")
            return False
            
        s3_key = '/'.join(parts[1:])
        
        # Delete from S3
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key
        )
        return True
    except Exception as e:
        st.error(f"Error deleting image from S3: {e}")
        return False

def check_s3_connection():
    """
    Check if we can connect to S3
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
        
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        return True
    except:
        st.error(f"Cannot connect to S3 bucket: {S3_BUCKET_NAME}")
        return False

def verify_s3_upload_functionality():
    """
    Verify that S3 upload functionality works
    
    Returns:
        tuple: (success, message)
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False, "Failed to connect to S3. Check your AWS credentials."
        
    try:
        # Create a small test image in memory
        from PIL import Image, ImageDraw
        import io
        
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "Test Image", fill=(255, 255, 255))
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Try uploading to S3
        test_key = f"test/test_image_{uuid.uuid4()}.png"
        
        s3_client.put_object(
            Body=img_bytes.getvalue(),
            Bucket=S3_BUCKET_NAME,
            Key=test_key,
            ContentType='image/png'
        )
        
        # Generate test URL and verify we can access it
        test_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{test_key}"
        
        # Verify we can access the image
        response = requests.head(test_url)
        if response.status_code == 200:
            # Clean up the test image
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=test_key)
            return True, "S3 upload and access test successful"
        else:
            return False, f"S3 upload succeeded but image is not accessible. Status: {response.status_code}"
            
    except Exception as e:
        return False, f"Error testing S3 upload: {e}"
