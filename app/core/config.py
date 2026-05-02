import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")

    RABBITMQ_URL = os.getenv("RABBITMQ_URL")
