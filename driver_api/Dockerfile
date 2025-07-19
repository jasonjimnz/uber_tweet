FROM python:3.10-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir fastapi uvicorn asyncpg pydantic python-dotenv pydantic-settings

EXPOSE 8001

# Command is specified in docker-compose.yml
# uvicorn api:app --host 0.0.0.0 --port 8001