FROM python:3.10-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir kafka-python requests python-dotenv

# Command is specified in docker-compose.yml
# python kafka_consumer.py