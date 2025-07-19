# Uber Tweet

## Fast context

Based on this tweet:

> You're building a food delivery app.
> 
> App tracks 100,000 drivers in real-time. 
> Chaos.
> 
> Driver's phone sends GPS coordinates every 4 seconds.
> 
> Drained phone batteries, your servers overwhelmed 🥵
> 
> How do you fix this?

I've quoted with this:

> MQTT - Postgres + PostGis - Kafka
> - Device sends its ID and geopos with MQTT (doesn't drain battery as HTTP Requests)
> - Kafka receives MQTT event
> - Using Postgres you store a state machine for every driver, and with PostGis you apply your geopositional logic

Then, suddenly I've made a hit tweet and I've talked with a lot of different people and,
we found that, maybe we need more context so, let's build **Uber Tweet**


## Problem

Based on the original tweet, we have a food delivery application, our application is
having two problems: the app drains the phone batteries due its geoposition and our
infra is suffering so hard and we have to fix that

## Possible root causes

- Phone battery drain because of geo position involves a lot of things: GPS itself,
    background services, how do you send your position, the frequency of sending your
    position to the backend
- The backend is receiving every 4 seconds the driver positions and it has at least
    100K drivers delivering food, that involves at least 3 actors in every delivery: 
    customers, restaurants and drivers. Also support could be involved so, with this
    numbers we could have up to 400K concurrent users, we will treat the main solution
    as a monolith so, the database will have some issues also before scaling up

## Possible solutions

- Use MQTT protocol in the mobile for reducing application resources usage
- Split monolith in few services for minimizing main DB operations, and gain
    some speedup using geospatial functionalities in DB (Postgres+PostGis) and
    managing write events with distributed message queue (Kafka), the new services
    will be done using FastAPI

## Developing the solution

### Customer side
For this "project," the mobile app will be mocked, we'll simulate the calls for
creating, confirming and delivering orders

### Application side

- We will need "something" to handle the MQTT messages, so we need a MQTT broker
    that will act as a proxy for Kafka
- We will need some logic for handling the Kafka events and write them in Postgres
    also, we need to handle some geospatial logic in the engine, so PostGis will help
    us on that purpose
- For giving the main backend a little bit of breath, we will do a small service using
    FastAPI that will retrieve information about the order

## Project Structure

The project consists of several services that work together:

1. **Zookeeper & Kafka**: Message broker system for handling driver position updates
2. **Mosquitto**: MQTT broker for receiving messages from drivers' mobile devices
3. **PostgreSQL with PostGIS**: Database for storing driver and order information with geospatial capabilities
4. **MQTT-Kafka Bridge**: Service that forwards messages from MQTT to Kafka
5. **Driver API**: Service for updating driver locations in the database
6. **Driver Events**: Service that processes driver location updates from Kafka
7. **Main API**: Service for tracking food deliveries

## Running with Docker

The easiest way to run the entire system is using Docker Compose:

```bash
docker-compose up -d
```

This will start all the services in the correct order. The services have dependencies configured to ensure they start only after their dependencies are ready.

### Potential Issues

If any containers fail to start, they will automatically restart due to the `restart: on-failure` policy. This is particularly important for services that depend on Kafka and Mosquitto, as they might need a moment to fully initialize.

If you encounter persistent issues, you can check the logs:

```bash
docker-compose logs <service_name>
```

## Database Initialization

The PostgreSQL database needs to be initialized with the correct schema and triggers. The SQL scripts for this are in the `sql` directory:

```bash
# Connect to the PostgreSQL container
docker exec -it uber_postgis bash

# Connect to the database
psql -U postgres -d food_delivery

# Run the initialization scripts copy the content and run it
# in the postgres console
# sql/food_delivery_ddl.sql
# sql/food_delivery_triggers.sql
```

Alternatively, you can use a database client like pgAdmin or DBeaver to connect to the database and run the scripts.

## Testing the System

Create an `.env` file with the following content:

```dotenv
# .env file
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/food_delivery

# --- NEW KAFKA & SERVICE CONFIG ---
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=driver-pos
DRIVER_API_URL=http://localhost:8001
```

Create it in `api`, `driver_api`, `driver_events`, `python_mqtt` folders

Once all containers are running and the database is initialized,
generate sample data, extract valid drivers and then you can 
generate valid driver position updates using the mqtt_producer:

```bash
# Consider adding ENVs first
python api/generate_data.py
python driver_extractor.py
python mqtt_producer.py
```

This will send a test message to the MQTT broker, which will be forwarded to Kafka and eventually update the driver's position in the database.

## Service Details

### MQTT Producer
- **Purpose**: Simulates a driver's mobile device sending location updates
- **Usage**: `python mqtt_producer.py`
- **Configuration**: Edit the variables at the top of the file to change broker settings

### MQTT-Kafka Bridge
- **Purpose**: Forwards messages from MQTT to Kafka
- **Configuration**: Environment variables in docker-compose.yml

### Driver API
- **Purpose**: Updates driver locations in the database
- **Endpoints**: 
  - PATCH `/drivers/{driver_id}/location`: Update a driver's location

### Driver Events
- **Purpose**: Processes driver location updates from Kafka
- **Configuration**: Environment variables in docker-compose.yml

### Main API
- **Purpose**: Provides delivery tracking information to customers
- **Endpoints**:
  - GET `/track/{order_id}`: Get the status and location of a delivery
