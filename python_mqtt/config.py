import os

MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "sensor/data")
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "mqtt_kafka_bridge")

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", 'localhost:9092')
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", 'driver-pos')
