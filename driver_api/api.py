import os
import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
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

class GeoPositionUpdate(BaseModel):
    latitude: float
    longitude: float

class DriverLocation(BaseModel):
    latitude: float
    longitude: float

class DriverStatusResponse(BaseModel):
    driver_id: UUID
    is_active: bool
    geoposition: DriverLocation
    last_updated_at: datetime

app = FastAPI(
    title="Driver Geoposition Service",
    description="An isolated service to update driver locations.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(settings.database_url)
        print("Driver service connected to database.")
    except Exception as e:
        print(f"🔥 Driver service failed to connect to database: {e}")
        db_pool = None

@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
        print("Driver service database connection pool closed.")

@app.patch("/drivers/{driver_id}/location",
           response_model=DriverStatusResponse,
           tags=["Driver"],
           summary="Update a driver's geoposition")
async def update_driver_location(
    driver_id: UUID,
    location_update: GeoPositionUpdate = Body(...),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    query = """
        UPDATE driver_status
        SET
            geoposition = ST_SetSRID(ST_MakePoint($1, $2), 4326),
            last_updated_at = NOW()
        WHERE driver_id = $3 and is_active = TRUE
        RETURNING
            driver_id,
            is_active,
            last_updated_at,
            ST_Y(geoposition::geometry) as latitude,
            ST_X(geoposition::geometry) as longitude;
    """
    record = await db.fetchrow(
        query,
        location_update.longitude,
        location_update.latitude,
        driver_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Status record for driver ID {driver_id} not found."
        )

    return DriverStatusResponse(
        driver_id=record['driver_id'],
        is_active=record['is_active'],
        last_updated_at=record['last_updated_at'],
        geoposition=DriverLocation(
            latitude=record['latitude'],
            longitude=record['longitude']
        )
    )
