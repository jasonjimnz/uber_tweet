import json
import logging
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from config import KAFKA_BOOTSTRAP_SERVERS

logger = logging.getLogger('mqtt_kafka_bridge')


class KafkaProducerWrapper:

    def __init__(self, bootstrap_servers=None):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.producer = self._create_producer()

    def _create_producer(self):
        try:
            logger.info("🔄 Initializing Kafka Producer...")
            producer = KafkaProducer(
                bootstrap_servers=[self.bootstrap_servers],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("✅ Kafka Producer Initialized.")
            return producer
        except NoBrokersAvailable:
            logger.error(
                f"❌ Kafka Error: No brokers available at {self.bootstrap_servers}. "
                "Is Kafka running?"
            )
            return None
        except Exception as e:
            logger.error(f"❌ Failed to create Kafka producer: {e}")
            return None

    def send_message(self, topic, message):
        if not self.producer:
            logger.warning("⚠️ Kafka producer not available, message not forwarded")
            return False

        try:
            self.producer.send(topic, value=message)
            self.producer.flush()
            logger.info(f"➡️ Forwarded to Kafka topic '{topic}'")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending message to Kafka: {e}")
            return False

    def close(self):
        if self.producer:
            self.producer.close()
            logger.info("✅ Kafka producer shut down.")
