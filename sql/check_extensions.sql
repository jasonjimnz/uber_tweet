-- Enable the PostGIS extension for geographic data types and functions
CREATE EXTENSION IF NOT EXISTS postgis;

-- Optional: Enable UUID generation function if not already available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";