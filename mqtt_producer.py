import json
import random
import time

import paho.mqtt.client as mqtt
from faker import Faker

MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sensor/data"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "sensor_producer")


def on_connect(**kwargs):
    rc = kwargs.get("rc")
    if rc == 0:
        print("✅ Successfully connected to MQTT Broker!")
    else:
        print(f"❌ Failed to connect, return code {rc}\n")


def on_publish(*args, **kwargs):
    mid = kwargs.get("mid")
    print(f"Message with mid {mid} published successfully.")


client.on_publish = on_publish

client.on_connect = on_connect
_faker = Faker()
lat, lon = _faker.latlng()
drivers = json.loads(open("drivers.json").read())
random_driver = random.choice(drivers)

def main():
    try:
        print(f"🔌 Connecting to MQTT Broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the broker running?")
        exit()
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        exit()

    client.loop_start()

    try:
        while True:
            payload = {
                "driver_id": random_driver,
                "timestamp": time.time(),
                "lat": float(lat),
                "lon": float(lon)
            }

            payload_json = json.dumps(payload)
            result = client.publish(MQTT_TOPIC, payload_json)
            status = result.rc

            if status == 0:
                print(f"✉️  Sent `{payload_json}` to topic `{MQTT_TOPIC}`")
                break
            else:
                print(f"Failed to send message to topic {MQTT_TOPIC}. Error code: {status}")

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down producer.")

    finally:
        client.loop_stop()
        client.disconnect()
        print("🔌 Disconnected from MQTT Broker.")


if __name__ == '__main__':
    main()
