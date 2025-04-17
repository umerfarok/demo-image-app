import os
from dotenv import load_dotenv
import pathlib

# Load environment variables
load_dotenv()

# Get the directory of this file for relative paths
CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql-11c2e19-product-gen.j.aivencloud.com'),
    'port': int(os.getenv('DB_PORT', '12629')),
    'user': os.getenv('DB_USER', 'avnadmin'),
    'password': os.getenv('DB_PASSWORD', 'AVNS_VEdxXziCXZ778Xm5Luo'),
    'database': os.getenv('DB_NAME', 'defaultdb'),
    'ssl_mode': os.getenv('DB_SSL_MODE', 'REQUIRED'),
    'ssl_ca': os.path.join(CURRENT_DIR, 'utils', os.getenv('DB_SSL_CA', 'ca.pem')),
    'ssl_verify': os.getenv('DB_SSL_VERIFY', 'true').lower() == 'true'
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
