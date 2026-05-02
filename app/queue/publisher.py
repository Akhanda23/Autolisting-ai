import json

from app.queue.rabbitmq import get_connection

def publish(exchange, routing_key, body):
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=exchange, exchange_type="topic",durable=True)

    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(body)
    )

    connection.close()