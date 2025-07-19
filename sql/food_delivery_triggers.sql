-- Remaining Time
-- This function calculates and updates the delivery time.
CREATE OR REPLACE FUNCTION update_remaining_time_func()
RETURNS TRIGGER AS $$
DECLARE
    -- Variable to hold the delivery record for the current driver
    active_delivery RECORD;
    -- Variable to hold the calculated distance in meters
    distance_meters FLOAT;
    -- Variable for the calculated remaining time in seconds
    new_remaining_time INT;
BEGIN
    -- Find the active delivery assigned to the driver whose position was just updated.
    -- We assume a driver can only have one delivery 'in_progress' at a time.
    SELECT INTO active_delivery
        dd.id AS delivery_id, o.delivery_address
    FROM driver_delivers dd
    JOIN orders o ON dd.order_id = o.id
    WHERE dd.driver_id = NEW.driver_id AND dd.delivery_status = 'in_progress'
    LIMIT 1;

    -- If an active delivery is found for this driver:
    IF FOUND THEN
        -- Calculate the distance between the driver's new geoposition and the order's delivery address.
        -- ST_Distance on GEOGRAPHY types returns the result in meters.
        distance_meters := ST_Distance(NEW.geoposition, active_delivery.delivery_address);

        -- Calculate remaining time based on the rule: 60 seconds per 100 meters.
        -- Formula: time = (distance / 100) * 60
        new_remaining_time := ROUND((distance_meters / 100.0) * 60.0);

        -- Update the remaining time in the driver_delivers table for the specific delivery.
        UPDATE driver_delivers
        SET remaining_time_seconds = new_remaining_time
        WHERE id = active_delivery.delivery_id;
    END IF;

    -- Return the NEW row to complete the trigger operation.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Driver Geoposition Status trigger

-- Create the trigger that will execute the function.
CREATE TRIGGER update_time_on_position_change
-- It fires AFTER any update operation on the driver_status table.
AFTER UPDATE ON driver_status
FOR EACH ROW
-- The WHEN condition ensures the trigger only runs if the driver is active
-- and either their geoposition or last_updated_at has changed.
WHEN (NEW.is_active = TRUE)
-- Execute the function defined above.
EXECUTE FUNCTION update_remaining_time_func();
