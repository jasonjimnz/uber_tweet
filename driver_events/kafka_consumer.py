import json
import logging
import os

import requests
from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] :: %(levelname)s :: %(message)s'
)
load_dotenv()
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "driver-pos,")
DRIVER_API_URL = os.getenv("DRIVER_API_URL", "http://localhost:8002")
logger = logging.getLogger('kafka_consumer')


def update_driver_location(driver_id: str, lat: float, lon: float):
    url = f"{DRIVER_API_URL}/drivers/{driver_id}/location"

    payload = {"latitude": lat, "longitude": lon}

    try:
        logger.info(f"Sending PATCH request to {url} with payload: {payload}...")
        response = requests.patch(url, json=payload, timeout=5)

        response.raise_for_status()

        logger.info(f"✅ Successfully updated location for driver {driver_id} to ({lat}, {lon})")

    except requests.exceptions.HTTPError as e:
        logger.info(f"🔥 HTTP Error for driver {driver_id}: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        logger.info(f"🔥 API Request Error for driver {driver_id}: {e}")


def main():
    logger.info("🚦 Kafka consumer starting...")
    logger.info(f"Connecting to Kafka at {KAFKA_SERVERS} on topic '{KAFKA_TOPIC}'")

    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_SERVERS,
        )
    except KafkaError as e:
        logger.info(f"🚨 Could not connect to Kafka: {e}")
        return

    logger.info("✅ Consumer connected. Waiting for messages...")

    try:
        logger.info("Waiting for messages... Press Ctrl+C to stop.")

        for message in consumer:
            data = json.loads(message.value.decode('utf-8'))
            logger.info(f"\n📩 Received message: {data}")

            if 'driver_id' in data and 'lat' in data and 'lon' in data:
                update_driver_location(
                    driver_id=data['driver_id'],
                    lat=data['lat'],
                    lon=data['lon']
                )
            else:
                logger.info(f"⚠️  Skipping malformed message: {data}")

    except KeyboardInterrupt:
        logger.info("\n🛑 Consumer stopped by user.")
    finally:
        consumer.close()
        logger.info("✅ Consumer closed.")


if __name__ == "__main__":
    logger.info("Starting up")
    main()
