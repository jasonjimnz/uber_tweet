import asyncio
import json
import os
import random

import asyncpg
from dotenv import load_dotenv
from faker import Faker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/food_delivery"


async def main():
    # Connect to the database
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Query all driver IDs from the drivers table
        query = "SELECT id FROM drivers"
        records = await conn.fetch(query)

        # Convert UUIDs to strings
        driver_ids = [str(record['id']) for record in records]

        # Store the IDs in drivers.json as an array of strings
        with open('drivers.json', 'w') as f:
            json.dump(driver_ids, f)

        print(f"✅ Successfully extracted {len(driver_ids)} driver IDs to drivers.json")
    finally:
        # Close the database connection
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
