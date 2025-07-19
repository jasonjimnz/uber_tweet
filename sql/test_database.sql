-- For simplicity, we'll hardcode UUIDs. In a real application,
-- you would capture the returned ID from one insert to use in the next.

-- 1. Insert a customer
INSERT INTO customers (id, full_name, phone_number, email)
VALUES ('a1b2c3d4-e5f6-7890-1234-567890abcdef', 'Ana García', '+34600111222', 'ana.garcia@email.com');

-- 2. Insert a restaurant (Location: Puerta del Sol, Madrid)
INSERT INTO restaurants (id, name, address, location)
VALUES ('b2c3d4e5-f6a7-8901-2345-67890abcdef1', 'Restaurante Sol', 'Puerta del Sol, 1, 28013 Madrid',
        -- ST_MakePoint takes (longitude, latitude)
        ST_SetSRID(ST_MakePoint(-3.703790, 40.416775), 4326));

-- 3. Insert a driver
INSERT INTO drivers (id, full_name, phone_number)
VALUES ('c3d4e5f6-a7b8-9012-3456-7890abcdef12', 'Carlos Ruiz', '+34611222333');

-- 4. Set the driver's initial status and position (near the restaurant)
-- The driver is set to active, ready to take deliveries.
INSERT INTO driver_status (driver_id, is_active, geoposition)
VALUES ('c3d4e5f6-a7b8-9012-3456-7890abcdef12', TRUE,
        ST_SetSRID(ST_MakePoint(-3.703500, 40.416500), 4326));

-- 5. Insert an order from the customer to the restaurant (Delivery: Plaza de Cibeles, Madrid)
INSERT INTO orders (id, customer_id, restaurant_id, delivery_address, order_details)
VALUES ('d4e5f6a7-b8c9-0123-4567-890abcdef123', 'a1b2c3d4-e5f6-7890-1234-567890abcdef', 'b2c3d4e5-f6a7-8901-2345-67890abcdef1',
        ST_SetSRID(ST_MakePoint(-3.692094, 40.419102), 4326),
        '{"items": [{"name": "Paella", "quantity": 1}, {"name": "Gazpacho", "quantity": 1}]}');

-- 6. Assign the order to the driver, marking it as 'in_progress'
-- The remaining_time_seconds is initially NULL. It will be populated by the trigger.
INSERT INTO driver_delivers (id, order_id, driver_id, delivery_status, remaining_time_seconds)
VALUES ('e5f6a7b8-c9d0-1234-5678-90abcdef1234', 'd4e5f6a7-b8c9-0123-4567-890abcdef123', 'c3d4e5f6-a7b8-9012-3456-7890abcdef12', 'in_progress');

UPDATE driver_status SET last_updated_at = NOW() WHERE driver_id = 'd4e5f6a7-b8c9-0123-4567-890abcdef123';