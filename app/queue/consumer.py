from app.queue.rabbitmq import get_connection


def consume(queue_name, callback):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=True
    )

    print(f"Listening on {queue_name}")
    channel.start_consuming()