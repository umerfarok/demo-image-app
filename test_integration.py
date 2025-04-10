import os
import sys
import pandas as pd
from PIL import Image, ImageDraw
import io
import requests
import uuid
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import application modules
from utils.api import save_uploaded_image, generate_mockup, is_s3_url
from utils.s3_storage import get_image_from_s3_url
from utils.export import export_to_csv

# Configure test settings
TEST_IMAGE_SIZE = (400, 400)
TEST_IMAGE_COLOR = 'blue'
TEST_TEXT_COLOR = 'white'
TEST_PRODUCT_NAME = "Test Product"
TEST_TEMPLATE_ID = "t-shirt"

def create_test_image():
    """Create a test image for upload"""
    img = Image.new('RGB', TEST_IMAGE_SIZE, color=TEST_IMAGE_COLOR)
    draw = ImageDraw.Draw(img)
    draw.text((50, 180), "Test Design", fill=TEST_TEXT_COLOR, font_size=40)
    
    # Save to BytesIO object
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Create a mock Streamlit uploaded file
    class MockUploadedFile:
        def __init__(self, content, filename, content_type):
            self.content = content
            self.name = filename
            self.type = content_type
            
        def getvalue(self):
            return self.content
            
        def getbuffer(self):
            return self.content
    
    return MockUploadedFile(img_bytes.getvalue(), "test_image.png", "image/png")

def test_full_workflow():
    """Test the complete workflow from upload to export"""
    print("Starting integration test...")
    
    # Step 1: Create and upload test image
    print("Step 1: Creating test image...")
    test_file = create_test_image()
    
    print("Step 2: Uploading test image...")
    image_path = save_uploaded_image(test_file)
    
    if not image_path:
        print("❌ Failed to upload test image")
        return False
        
    print(f"✅ Image uploaded: {image_path}")
    
    # Step 3: Generate mockup
    print("Step 3: Generating mockup...")
    mockup_url = generate_mockup(image_path, TEST_TEMPLATE_ID, is_s3_url(image_path))
    
    if not mockup_url:
        print("❌ Failed to generate mockup")
        return False
        
    print(f"✅ Mockup generated: {mockup_url}")
    
    # Step 4: Create test product data
    print("Step 4: Creating test product data...")
    test_product = pd.DataFrame([{
        'id': 999,
        'product_name': TEST_PRODUCT_NAME,
        'item_sku': f"TST-{uuid.uuid4().hex[:6].upper()}",
        'parent_child': 'Parent',
        'parent_sku': None,
        'size': 'M',
        'color': 'Blue',
        'image_url': mockup_url,
        'marketplace_title': 'Test Product For Marketplace',
        'category': 'Test Category',
        'tax_class': 'Standard',
        'quantity': 10,
        'price': 19.99,
        'created_at': pd.Timestamp.now()
    }])
    
    # Step 5: Test CSV export
    print("Step 5: Testing CSV export...")
    csv_data = export_to_csv(test_product)
    
    if not csv_data:
        print("❌ Failed to export CSV")
        return False
    
    # Verify CSV contains image URL
    csv_str = csv_data.decode('utf-8')
    if mockup_url not in csv_str:
        print("❌ CSV export doesn't contain mockup URL")
        return False
        
    print("✅ CSV export successful and contains the mockup URL")
    
    # Step 6: Verify image accessibility 
    print("Step 6: Verifying mockup image is accessible...")
    if is_s3_url(mockup_url):
        response = requests.head(mockup_url)
        if response.status_code != 200:
            print(f"❌ Mockup image not accessible. Status code: {response.status_code}")
            return False
    else:
        if not os.path.exists(mockup_url):
            print("❌ Mockup image file not found")
            return False
            
    print("✅ Mockup image is accessible")
    
    print("\n✅ All tests PASSED! The application is working correctly.")
    return True

if __name__ == "__main__":
    test_full_workflow()
