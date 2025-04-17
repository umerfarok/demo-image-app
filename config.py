import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'product_generator')
}

# API configuration
API_KEY = os.getenv('DYNAMIC_MOCKUPS_API_KEY', '')
API_URL = 'https://api.dynamicmockups.com/v1'

# Storage configuration - S3 is now primary method
IMAGES_DIR = 'images'  # Used only if S3 setup fails
USE_S3_STORAGE = False

# AWS S3 configuration
S3_CONFIG = {
    'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'region_name': os.getenv('AWS_REGION', 'us-east-1'),
    'bucket_name': os.getenv('S3_BUCKET_NAME')
}

# Hard-coded credentials for single user (in production, use more secure methods)
USER_EMAIL = 'admin@example.com'
USER_PASSWORD = 'password123'
