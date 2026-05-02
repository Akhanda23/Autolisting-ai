import json
import mimetypes
import time
import io
from PIL import Image

from rembg import remove

from app.storage.s3_client import download_file, upload_file
from app.queue.publisher import publish


# ----------------------------
# Helpers
# ----------------------------

def safe_download(file_key: str, retries: int = 3):
    last_error = None

    for i in range(retries):
        try:
            image = download_file(file_key)

            if not image:
                raise Exception("Empty file returned from storage")

            return image

        except Exception as e:
            last_error = e
            time.sleep(1 * (i + 1))  # exponential-ish backoff

    raise Exception(f"S3_DOWNLOAD_FAILED: {str(last_error)}")


def validate_image(image_bytes: bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()  # validates corruption without fully decoding
    except Exception as e:
        raise Exception(f"INVALID_IMAGE_FILE: {str(e)}")


def safe_mime(file_key: str):
    content_type, _ = mimetypes.guess_type(file_key)
    return content_type or "application/octet-stream"


def process_car(car_id: str, file_key: str):
    try:
        # 1. Download image (with retry)
        image = safe_download(file_key)

        # 2. Validate image
        validate_image(image)

        # 3. Background removal
        try:
            bg_removed = remove(image)
        except Exception as e:
            raise Exception(f"REMBG_FAILED: {str(e)}")

        # 4. Upload result
        bg_key = f"bg-{file_key}"
        content_type = safe_mime(file_key)

        upload_file(bg_key, bg_removed, content_type)

        # 5. Publish success event
        publish(
            exchange="car_events",
            routing_key="bg.done",
            body=json.dumps({
                "carId": car_id,
                "originalKey": file_key,
                "bgKey": bg_key
            })
        )

        print("✅ Background removal completed")

    except Exception as e:
        print(f"⚠️ Error processing car {car_id}: {str(e)}")
        # structured failure event
        publish(
            exchange="car_events",
            routing_key="job.failed",
            body=json.dumps({
                "carId": car_id,
                "fileKey": file_key,
                "stage": "image_processing",
                "error": str(e)
            })
        )

        print(f"❌ Job failed: {str(e)}")
        raise