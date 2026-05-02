import json
from app.pipelines.car_pipeline import process_car
from app.queue.rabbitmq import get_connection

def image_callback(ch, method, properties, body):
    data = json.loads(body)
    print(f"Received image for {data['carAnalysisId']}")
    process_car(data["carAnalysisId"], data["fileKey"])

def analysis_callback(ch, method, properties, body):
    data = json.loads(body)
    # analyze_car(data["carAnalysisId"], data["fileKey"])
    print(f"Received analysis result for {data['carAnalysisId']}")
    # run car detection

def pitch_callback(ch, method, properties, body):
    data = json.loads(body)
    # generate AI pitch

def start_worker():
    connection = get_connection()
    channel = connection.channel()

    channel.basic_consume(queue="IMAGE_UPLOAD", on_message_callback=image_callback, auto_ack=True)
    channel.basic_consume(queue="CAR_ANALYSIS", on_message_callback=analysis_callback, auto_ack=True)
    # channel.basic_consume(queue="AI_PITCH", on_message_callback=pitch_callback, auto_ack=True)

    print("🚀 Listening to 3 queues...")
    channel.start_consuming()