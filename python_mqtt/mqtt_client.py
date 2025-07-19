"""
MQTT client module for the MQTT-Kafka bridge.

This module provides functionality to create and manage an MQTT client
that forwards messages to Kafka.
"""

import json
import logging
import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_TOPIC,
    MQTT_CLIENT_ID,
    KAFKA_TOPIC
)

logger = logging.getLogger('mqtt_kafka_bridge')


class MQTTClient:
    """
    MQTT client that subscribes to topics and forwards messages to Kafka.

    This class encapsulates the MQTT client creation, connection, and message handling.
    """

    def __init__(self, kafka_producer, broker_host=None, broker_port=None, 
                 topic=None, client_id=None):
        """
        Initialize the MQTT client.

        Args:
            kafka_producer: Kafka producer instance to forward messages to
            broker_host (str, optional): MQTT broker host. Defaults to config value.
            broker_port (int, optional): MQTT broker port. Defaults to config value.
            topic (str, optional): MQTT topic to subscribe to. Defaults to config value.
            client_id (str, optional): MQTT client ID. Defaults to config value.
        """
        self.kafka_producer = kafka_producer
        self.broker_host = broker_host or MQTT_BROKER_HOST
        self.broker_port = broker_port or MQTT_BROKER_PORT
        self.topic = topic or MQTT_TOPIC
        self.client_id = client_id or MQTT_CLIENT_ID

        # Create MQTT client
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            self.client_id,
            userdata={'kafka_producer': self.kafka_producer}
        )

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties=None, *args, **kwargs):
        """
        Callback for when the client connects to the broker.

        Args:
            client: MQTT client instance
            userdata: User data passed to the client
            flags: Connection flags
            rc: Connection result code
            properties: Connection properties (MQTT v5.0)
        """
        if rc == 0:
            logger.info("✅ Successfully connected to MQTT Broker!")
            logger.info(f"👂 Subscribing to topic: {self.topic}")
            client.subscribe(self.topic)
        else:
            logger.error(f"❌ Failed to connect to MQTT broker, return code {rc}")

    def _on_message(self, client, userdata, msg, properties=None, *args, **kwargs):
        """
        Callback for when a message is received from the broker.

        Args:
            client: MQTT client instance
            userdata: User data passed to the client
            msg: Received message
            properties: Message properties (MQTT v5.0)
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        try:
            logger.info(f"📩 Received message on topic {msg.topic}")
            payload = msg.payload.decode('utf-8')

            # Try to parse as JSON
            try:
                payload_dict = json.loads(payload)
                logger.info(f"📦 Message payload: {payload_dict}")

                # Forward to Kafka
                kafka_producer = userdata.get('kafka_producer')
                if kafka_producer:
                    kafka_producer.send_message(KAFKA_TOPIC, payload_dict)
                else:
                    logger.warning("⚠️ Kafka producer not available, message not forwarded")

            except json.JSONDecodeError:
                logger.warning(f"⚠️ Could not decode JSON from payload: {payload}")

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    def _on_disconnect(self, client, userdata, rc, properties=None, *args, **kwargs):
        """
        Callback for when the client disconnects from the broker.

        Args:
            client: MQTT client instance
            userdata: User data passed to the client
            rc: Disconnection result code
            properties: Disconnection properties (MQTT v5.0)
        """
        if rc == 0:
            logger.info("🔌 Disconnected from MQTT Broker")
        else:
            logger.warning(f"⚠️ Unexpected disconnection from MQTT Broker, code: {rc}")

    def connect(self):
        """
        Connect to the MQTT broker.

        Returns:
            bool: True if connection was successful, False otherwise.
        """
        try:
            logger.info(f"🔌 Connecting to MQTT Broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            return True
        except ConnectionRefusedError:
            logger.error("❌ Connection refused. Is the MQTT broker running?")
            return False
        except Exception as e:
            logger.error(f"❌ An error occurred while connecting: {e}")
            return False

    def start(self):
        """
        Start the MQTT client loop.

        This method blocks until disconnect() is called or an error occurs.
        """
        try:
            logger.info("🔄 Starting MQTT client loop...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received. Shutting down...")
        except Exception as e:
            logger.error(f"❌ An error occurred in the main loop: {e}")
        finally:
            self.disconnect()

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.disconnect()
        logger.info("✅ MQTT client disconnected.")
