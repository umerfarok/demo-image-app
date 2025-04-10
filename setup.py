import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import mysql.connector
import streamlit as st

# Load environment variables
load_dotenv()

def check_env_variables():
    """Check if all required environment variables are set"""
    required_vars = [
        'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
        'DYNAMIC_MOCKUPS_API_KEY',
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'S3_BUCKET_NAME'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    return missing

def check_database_connection():
    """Test database connection"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        
        if conn.is_connected():
            print("✅ Database connection successful")
            conn.close()
            return True
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_s3_connection():
    """Test S3 connection and bucket access"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        
        # Test if bucket exists and is accessible
        s3_client.head_bucket(Bucket=os.getenv('S3_BUCKET_NAME'))
        print(f"✅ S3 bucket '{os.getenv('S3_BUCKET_NAME')}' is accessible")
        
        # Check if required folders exist, create if they don't
        folders = ['original', 'mockups']
        for folder in folders:
            try:
                s3_client.head_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=f"{folder}/")
                print(f"✅ Folder '{folder}' exists in S3 bucket")
            except ClientError:
                # Create the folder if it doesn't exist
                s3_client.put_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=f"{folder}/")
                print(f"✅ Created folder '{folder}' in S3 bucket")
        
        return True
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def setup_app():
    """Run all setup checks and create necessary resources"""
    print("🔍 Checking application setup...")
    
    # Check environment variables
    missing_vars = check_env_variables()
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the required variables.")
        return False
    else:
        print("✅ All environment variables are set")
    
    # Check database connection
    db_ok = check_database_connection()
    if not db_ok:
        print("Please check your database configuration.")
        return False
    
    # Check S3 connection
    s3_ok = check_s3_connection()
    if not s3_ok:
        print("Please check your AWS S3 configuration.")
        return False
        
    # Test S3 upload functionality
    print("\n🔍 Testing S3 upload functionality...")
    from utils.s3_storage import verify_s3_upload_functionality
    s3_upload_ok, s3_upload_msg = verify_s3_upload_functionality()
    if s3_upload_ok:
        print(f"✅ {s3_upload_msg}")
    else:
        print(f"❌ {s3_upload_msg}")
        print("S3 integration issues found. Images may not upload or be accessible.")
        return False
    
    # Test API connection
    print("\n🔍 Testing DynamicMockups API connectivity...")
    from utils.api import verify_api_functionality
    api_ok, api_msg = verify_api_functionality()
    if api_ok:
        print(f"✅ {api_msg}")
    else:
        print(f"❌ {api_msg}")
        print("API integration issues found. Mockups may not generate correctly.")
        return False
    
    # Test CSV export functionality
    print("\n🔍 Testing CSV export functionality...")
    from utils.export import verify_export_functionality
    export_ok, export_msg = verify_export_functionality()
    if export_ok:
        print(f"✅ {export_msg}")
    else:
        print(f"❌ {export_msg}")
        print("CSV export issues found. Exports may not contain all required fields.")
        return False
    
    # Test complete workflow (optional - could be too heavy for setup)
    # This would upload an image, generate a mockup, and attempt to export
    
    print("\n✅ All tests passed! The application is ready to run.")
    print("Run 'streamlit run app.py' to start the application.")
    return True

if __name__ == "__main__":
    setup_app()
