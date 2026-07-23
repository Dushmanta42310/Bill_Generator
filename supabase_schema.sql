-- PostgreSQL database schema definition for RIDES table in Supabase
-- Paste this script into the Supabase SQL Editor (Dashboard > SQL Editor > New query) and run it.

CREATE TABLE IF NOT EXISTS rides (
    ride_id VARCHAR(30) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    time_of_ride TIMESTAMP WITH TIME ZONE NOT NULL,
    distance_km NUMERIC(5, 2) NOT NULL,
    duration_min NUMERIC(5, 2) NOT NULL,
    pickup_address VARCHAR(500) NOT NULL,
    drop_address VARCHAR(500) NOT NULL,
    total_amount NUMERIC(8, 2) NOT NULL,
    ride_charge NUMERIC(8, 2) NOT NULL,
    booking_fees NUMERIC(8, 2) NOT NULL,
    convenience_charges NUMERIC(8, 2) NOT NULL,
    gateway_charges NUMERIC(8, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    captain_name VARCHAR(100) NOT NULL,
    vehicle_number VARCHAR(30) NOT NULL,
    invoice_no VARCHAR(30) NOT NULL,
    state VARCHAR(50) NOT NULL,
    captain_fee NUMERIC(8, 2) NOT NULL,
    ride_cgst NUMERIC(8, 2) NOT NULL,
    ride_sgst NUMERIC(8, 2) NOT NULL,
    booking_cgst NUMERIC(8, 2) NOT NULL,
    booking_sgst NUMERIC(8, 2) NOT NULL
);

-- Index for faster search on customer name and ride time
CREATE INDEX IF NOT EXISTS idx_rides_customer_name ON rides(customer_name);
CREATE INDEX IF NOT EXISTS idx_rides_time ON rides(time_of_ride);

-- Enable Row Level Security (RLS)
ALTER TABLE rides ENABLE ROW LEVEL SECURITY;

-- Create Policies to allow public CRUD operations (useful if using the Publishable Anon Key)
-- Warning: This allows anyone with the anon key to read, insert, and delete. 
-- In a production environment with sensitive user data, restrict these policies using authenticated users.

CREATE POLICY "Allow public select access" ON rides
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public insert access" ON rides
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public delete access" ON rides
    FOR DELETE
    USING (true);
