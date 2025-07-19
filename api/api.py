import os
import asyncpg
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL")

settings = Settings()

db_pool: Optional[asyncpg.Pool] = None

async def get_db_connection() -> asyncpg.Connection:
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection is not available.")
    async with db_pool.acquire() as connection:
        yield connection

class DriverLocation(BaseModel):
    latitude: float
    longitude: float

class DeliveryTrackingResponse(BaseModel):
    order_id: UUID
    delivery_status: str
    restaurant_name: str
    driver_name: Optional[str] = None
    remaining_time_seconds: Optional[int] = None
    driver_location: Optional[DriverLocation] = None

    class Config:
        form_attributes = True

app = FastAPI(
    title="Food Delivery Tracking API",
    description="API for customers to track their food delivery in real-time.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(settings.database_url)
        print("Database connection pool created successfully.")
    except Exception as e:
        print(f"🔥 Failed to create database connection pool: {e}")
        db_pool = None

@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
        print("Database connection pool closed.")

@app.get("/track/{order_id}",
         response_model=DeliveryTrackingResponse,
         tags=["Tracking"],
         summary="Track a delivery by Order ID")
async def track_delivery(order_id: UUID, db: asyncpg.Connection = Depends(get_db_connection)):
    query = """
            SELECT dd.order_id,
                   dd.delivery_status,
                   ROUND((ST_Distance(ds.geoposition::geography, o.delivery_address::geography) / 100.0) * 60.0) AS remaining_time_seconds,
                   d.full_name                    AS driver_name,
                   r.name                         AS restaurant_name,

                   ST_Y(ds.geoposition::geometry) AS driver_latitude,
                   ST_X(ds.geoposition::geometry) AS driver_longitude
            FROM driver_delivers dd 
                     JOIN orders o ON dd.order_id = o.id 
                     JOIN restaurants r ON o.restaurant_id = r.id 
                -- LEFT JOINs are used for driver info, as an order might be assigned but not yet in progress 
                     LEFT JOIN drivers d ON dd.driver_id = d.id 
                     LEFT JOIN driver_status ds ON dd.driver_id = ds.driver_id AND ds.is_active = TRUE
            WHERE dd.order_id = $1; 
            """
    record = await db.fetchrow(query, order_id)

    if not record:
        raise HTTPException(status_code=404, detail="Order not found.")

    driver_location = None
    if record["driver_latitude"] and record["driver_longitude"]:
        driver_location = DriverLocation(
            latitude=record["driver_latitude"],
            longitude=record["driver_longitude"]
        )
    return DeliveryTrackingResponse(
        order_id=record["order_id"],
        delivery_status=record["delivery_status"],
        restaurant_name=record["restaurant_name"],
        driver_name=record["driver_name"],
        remaining_time_seconds=record["remaining_time_seconds"],
        driver_location=driver_location
    )
