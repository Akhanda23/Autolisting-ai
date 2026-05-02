import boto3
import os
from app.core.config import Config

s3 = boto3.client(
    "s3",
    aws_access_key_id=Config.AWS_ACCESS_KEY,
    aws_secret_access_key=Config.AWS_SECRET_KEY,
    region_name=Config.AWS_REGION,

    # 🔥 CRITICAL FOR SUPABASE
    endpoint_url="https://htdluxgjqyvdrgzdhnem.storage.supabase.co/storage/v1/s3",
)

def download_file(key):
    obj = s3.get_object(Bucket=Config.S3_BUCKET, Key=key)
    return obj["Body"].read()

def upload_file(key, data, content_type="image/png"):
    s3.put_object(Bucket=Config.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{Config.S3_ENDPOINT}/{Config.S3_BUCKET}/{key}"