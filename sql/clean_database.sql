-- This statement clears the main tables and automatically cascades the operation
-- to all dependent tables (orders, driver_status, driver_delivers).
-- RESTART IDENTITY resets any sequences, which is good practice.
TRUNCATE TABLE
    customers,
    restaurants,
    drivers
RESTART IDENTITY CASCADE;