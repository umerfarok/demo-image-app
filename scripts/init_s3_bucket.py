import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def create_s3_bucket():
    """Create an S3 bucket for product images with public read access"""
    
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        print("Error: Missing AWS credentials or bucket name. Check your .env file.")
        return False
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Create bucket with appropriate configuration
        if AWS_REGION == 'us-east-1':
            # Special case for us-east-1 region
            response = s3_client.create_bucket(
                Bucket=S3_BUCKET_NAME,
                ACL='private'  # Start with private, we'll set permissions via policy
            )
        else:
            # For other regions
            response = s3_client.create_bucket(
                Bucket=S3_BUCKET_NAME,
                ACL='private',
                CreateBucketConfiguration={
                    'LocationConstraint': AWS_REGION
                }
            )
        
        print(f"S3 bucket '{S3_BUCKET_NAME}' created successfully!")
        
        # Set up bucket policy for public read access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadForGetBucketObjects",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
                }
            ]
        }
        
        # Convert policy to JSON string
        import json
        bucket_policy_string = json.dumps(bucket_policy)
        
        # Set bucket policy
        s3_client.put_bucket_policy(
            Bucket=S3_BUCKET_NAME,
            Policy=bucket_policy_string
        )
        
        print(f"Bucket policy set to allow public read access")
        
        # Create folders in the bucket
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key='original/'
        )
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key='mockups/'
        )
        
        print(f"Created 'original' and 'mockups' folders in the bucket")
        
        # Enable CORS for the bucket to allow web access
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }]
        }
        
        s3_client.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        
        print(f"CORS configuration set for the bucket")
        
        print(f"\nYour S3 bucket is now ready to use!")
        print(f"Base URL for images: https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"Bucket '{S3_BUCKET_NAME}' already exists and is owned by you.")
            return True
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"Bucket '{S3_BUCKET_NAME}' already exists but is owned by another AWS account.")
            return False
        else:
            print(f"Error creating bucket: {e}")
            return False

if __name__ == "__main__":
    print("Initializing S3 bucket for product images...")
    create_s3_bucket()
