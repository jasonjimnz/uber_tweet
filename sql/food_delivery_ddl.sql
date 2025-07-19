-- Stores information about customers
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stores information about restaurants, including their location
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    -- GEOGRAPHY type is used for geographic coordinates (Longitude, Latitude)
    -- SRID 4326 is the standard for GPS coordinates (WGS 84)
    location GEOGRAPHY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Create a spatial index for faster location-based queries
CREATE INDEX restaurants_location_idx ON restaurants USING GIST (location);


-- Stores information about delivery drivers
CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tracks the real-time status and location of a driver
CREATE TABLE driver_status (
    driver_id UUID PRIMARY KEY,
    is_active BOOLEAN DEFAULT FALSE,
    -- Current geographic position of the driver
    geoposition GEOGRAPHY(Point, 4326),
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_driver
        FOREIGN KEY(driver_id)
        REFERENCES drivers(id)
        ON DELETE CASCADE -- If a driver is deleted, their status is also deleted
);
-- Create a spatial index for faster geoposition lookups
CREATE INDEX driver_status_geoposition_idx ON driver_status USING GIST (geoposition);


-- Stores information about orders placed by customers
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL,
    restaurant_id UUID NOT NULL,
    -- The destination address for the delivery
    delivery_address GEOGRAPHY(Point, 4326) NOT NULL,
    order_details JSONB, -- Flexible field for order items (e.g., [{"item": "Pizza", "quantity": 1}])
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_customer
        FOREIGN KEY(customer_id) REFERENCES customers(id),
    CONSTRAINT fk_restaurant
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
);
-- Create a spatial index for delivery addresses
CREATE INDEX orders_delivery_address_idx ON orders USING GIST (delivery_address);


-- Junction table to assign a driver to an order and track delivery
CREATE TABLE driver_delivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL UNIQUE, -- An order can only be delivered once
    driver_id UUID NOT NULL,
    -- Status of the delivery: e.g., 'assigned', 'in_progress', 'delivered', 'cancelled'
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'assigned',
    -- Estimated time remaining for delivery, stored in seconds
    remaining_time_seconds INT,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT fk_order
        FOREIGN KEY(order_id) REFERENCES orders(id),
    CONSTRAINT fk_driver
        FOREIGN KEY(driver_id) REFERENCES drivers(id)
);