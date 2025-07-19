import sys
import logging

from logger import setup_logger
from kafka_producer import KafkaProducerWrapper
from mqtt_client import MQTTClient


def main():
    logger = setup_logger()

    logger.info("Starting MQTT-Kafka bridge...")
    kafka_producer = KafkaProducerWrapper()
    if not kafka_producer.producer:
        logger.error("❌ Failed to create Kafka producer. Exiting.")
        return 1

    mqtt_client = MQTTClient(kafka_producer)

    if not mqtt_client.connect():
        logger.error("❌ Failed to connect to MQTT broker. Exiting.")
        kafka_producer.close()
        return 1

    try:
        mqtt_client.start()
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received. Shutting down...")
    except Exception as e:
        logger.error(f"❌ An error occurred in the main loop: {e}")
        return 1
    finally:
        mqtt_client.disconnect()
        kafka_producer.close()
        logger.info("✅ MQTT-Kafka bridge shut down.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
