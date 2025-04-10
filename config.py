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

# App configuration
IMAGES_DIR = 'images'

# Hard-coded credentials for single user (in production, use more secure methods)
USER_EMAIL = 'admin@example.com'
USER_PASSWORD = 'password123'
