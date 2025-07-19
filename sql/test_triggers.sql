-- 1 Initial State
SELECT remaining_time_seconds
FROM driver_delivers
WHERE order_id = 'd4e5f6a7-b8c9-0123-4567-890abcdef123';
-- 2 Driver's Geoposition
-- The driver moves from near Puerta del Sol towards Plaza de Cibeles.
UPDATE driver_status
SET geoposition = ST_SetSRID(ST_MakePoint(-3.698000, 40.417800), 4326)
WHERE driver_id = 'c3d4e5f6-a7b8-9012-3456-7890abcdef12';
-- 3 Verifiying trigger after geoposition update
-- Check the updated time
SELECT remaining_time_seconds
FROM driver_delivers
WHERE order_id = 'd4e5f6a7-b8c9-0123-4567-890abcdef123';

-- 4 Update only the last_updated_at field
UPDATE driver_status
SET last_updated_at = NOW()
WHERE driver_id = 'c3d4e5f6-a7b8-9012-3456-7890abcdef12';

-- 5 Verifiying trigger after time update
-- Check the updated time again
SELECT remaining_time_seconds
FROM driver_delivers
WHERE order_id = 'd4e5f6a7-b8c9-0123-4567-890abcdef123';
