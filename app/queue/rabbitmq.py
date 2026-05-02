import pika
from app.core.config import Config

def get_connection():
    return pika.BlockingConnection(
        pika.URLParameters(Config.RABBITMQ_URL)
    )