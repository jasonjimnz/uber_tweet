import asyncio
import json
import os
import random

import asyncpg
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

NUM_CUSTOMERS = 50
NUM_RESTAURANTS = 20
NUM_DRIVERS = 15
NUM_ORDERS = 100

fake = Faker()

SAMPLE_FOOD_ITEMS = [
    "Pepperoni Pizza",
    "Classic Cheeseburger",
    "French Fries",
    "Buffalo Wings",
    "Fried Chicken Bucket",
    "Mac & Cheese",
    "Beef Tacos",
    "Chicken Burrito",
    "Caesar Salad",
    "Onion Rings",
    "Chocolate Milkshake",
    "Club Sandwich",
    "BBQ Ribs",
    "Loaded Nachos",
    "Classic Hot Dog"
]


async def clear_database(conn):
    print("🗑️  Clearing existing data from all tables...")
    await conn.execute("""
                       TRUNCATE TABLE
                           customers,
            restaurants,
            drivers
        RESTART IDENTITY CASCADE;
                       """)
    print("✅  Database cleared successfully.")


async def generate_customers(conn: asyncpg.Connection, count):
    print(f"👤  Generating {count} customers...")
    customers_data = []
    for _ in range(count):
        customers_data.append({
            "full_name": fake.name(),
            "phone_number": fake.unique.phone_number().split('x')[0],
            "email": fake.unique.email()
        })
    query = "INSERT INTO customers (full_name, phone_number, email) VALUES ($1, $2, $3) RETURNING id"

    records = await conn.fetchmany(query, [(c["full_name"], c["phone_number"], c["email"]) for c in customers_data])

    return [r['id'] for r in records]


async def generate_restaurants(conn, count):
    print(f"🍽️  Generating {count} restaurants...")
    restaurants_data = []
    for _ in range(count):
        lon, lat = fake.local_latlng(country_code="US", coords_only=True)
        restaurants_data.append({
            "name": f"Restaurante {fake.last_name()}",
            "address": fake.address(),
            "location": f"POINT({lon} {lat})"
        })

    query = "INSERT INTO restaurants (name, address, location) VALUES ($1, $2, ST_SetSRID(ST_GeomFromText($3), 4326)) RETURNING id"
    records = await conn.fetchmany(query, [(r["name"], r["address"], r["location"]) for r in restaurants_data])

    return [r['id'] for r in records]


async def generate_drivers(conn: asyncpg.Connection, count):
    print(f"🚚  Generating {count} drivers and their status...")
    drivers_data = []
    for _ in range(count):
        drivers_data.append({
            "full_name": fake.name(),
            "phone_number": fake.unique.phone_number().split('x')[0]
        })

    query = "INSERT INTO drivers (full_name, phone_number) VALUES ($1, $2) RETURNING id"
    records = await conn.fetchmany(
        query,
        [(d["full_name"], d["phone_number"]) for d in drivers_data]

    )

    driver_ids = [r['id'] for r in records]

    driver_status_data = []
    for driver_id in driver_ids:
        lon, lat = fake.local_latlng(country_code="US", coords_only=True)
        driver_status_data.append({
            "driver_id": driver_id,
            "is_active": True,
            "geoposition": f"POINT({lon} {lat})"
        })

    status_query = "INSERT INTO driver_status (driver_id, is_active, geoposition) VALUES ($1, $2, ST_SetSRID(ST_GeomFromText($3), 4326))"
    await conn.fetchmany(
        status_query,
        [(s["driver_id"], s["is_active"], s["geoposition"]) for s in
         driver_status_data])
    return driver_ids


async def generate_orders_and_deliveries(conn, count, customer_ids, restaurant_ids, driver_ids):
    print(f"📝  Generating {count} orders and deliveries...")
    for _ in range(count):
        customer_id = random.choice(customer_ids)
        restaurant_id = random.choice(restaurant_ids)
        lon, lat = fake.local_latlng(country_code="US", coords_only=True)
        delivery_address = f"POINT({lon} {lat})"
        order_details = json.dumps({
            "items": [{"name": random.choice(SAMPLE_FOOD_ITEMS), "quantity": random.randint(1, 3)}]
        })

        order_query = """
                      INSERT INTO orders (customer_id, restaurant_id, delivery_address, order_details)
                      VALUES ($1, $2, ST_SetSRID(ST_GeomFromText($3), 4326), $4) RETURNING id \
                      """
        order_id = await conn.fetchval(order_query, customer_id, restaurant_id, delivery_address, order_details)

        driver_id = random.choice(driver_ids)
        status = random.choice(['assigned', 'in_progress', 'delivered'])

        completed_at = "NOW()" if status == 'delivered' else "NULL"

        delivery_query = f"""
            INSERT INTO driver_delivers (order_id, driver_id, delivery_status, completed_at)
            VALUES ($1, $2, $3, {completed_at})
        """
        await conn.execute(delivery_query, order_id, driver_id, status)


async def calculate_initial_delivery_times(conn):
    print("\n⏱️  Calculating initial remaining times for 'in_progress' deliveries...")

    distance_query = """
                     SELECT dd.id                                           as delivery_id, 
                            ST_Distance(ds.geoposition, o.delivery_address) as distance_meters
                     FROM driver_delivers dd
                              JOIN orders o ON dd.order_id = o.id
                              JOIN driver_status ds ON dd.driver_id = ds.driver_id
                     WHERE dd.delivery_status = 'in_progress'
                       AND ds.is_active = TRUE
                       AND dd.remaining_time_seconds IS NULL; 
                     """
    records = await conn.fetch(distance_query)

    if not records:
        print("🤷  No deliveries need initial time calculation.")
        return

    update_data = []
    for record in records:
        time_seconds = round((record['distance_meters'] / 100.0) * 60.0)
        update_data.append((time_seconds, record['delivery_id']))

    update_query = "UPDATE driver_delivers SET remaining_time_seconds = $1 WHERE id = $2"
    await conn.executemany(update_query, update_data)

    print(f"✅  Calculated initial times for {len(update_data)} deliveries.")


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await clear_database(conn)

        customer_ids = await generate_customers(conn, NUM_CUSTOMERS)
        print(f"✅  Successfully inserted {len(customer_ids)} customers.\n")

        restaurant_ids = await generate_restaurants(conn, NUM_RESTAURANTS)
        print(f"✅  Successfully inserted {len(restaurant_ids)} restaurants.\n")

        driver_ids = await generate_drivers(conn, NUM_DRIVERS)
        print(f"✅  Successfully inserted {len(driver_ids)} drivers.\n")

        await generate_orders_and_deliveries(conn, NUM_ORDERS, customer_ids, restaurant_ids, driver_ids)
        print(f"✅  Successfully inserted {NUM_ORDERS} orders and deliveries.\n")

        await calculate_initial_delivery_times(conn)
        print("🎉  All data generated successfully!")

    except Exception as e:
        print(f"🔥 An error occurred: {e}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
