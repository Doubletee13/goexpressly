-- GoExpressly DB Migration
-- Adds sender/origin, recipient/destination, and geolocation columns to packages table.
-- Safe to run multiple times (uses IF NOT EXISTS).
-- Run this against your PostgreSQL database before restarting the backend.

ALTER TABLE packages
  ADD COLUMN IF NOT EXISTS sender_name         VARCHAR(255),
  ADD COLUMN IF NOT EXISTS sender_phone        VARCHAR(50),
  ADD COLUMN IF NOT EXISTS sender_address      TEXT,
  ADD COLUMN IF NOT EXISTS city_collection     VARCHAR(255),
  ADD COLUMN IF NOT EXISTS shipping_date       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS shipping_quantity   INTEGER,
  ADD COLUMN IF NOT EXISTS weight_lbs          DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS carrier             VARCHAR(255),
  ADD COLUMN IF NOT EXISTS delivery_city       VARCHAR(255),
  ADD COLUMN IF NOT EXISTS destination_address TEXT,
  ADD COLUMN IF NOT EXISTS estimated_delivery_date TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS current_lat         DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS current_lng         DOUBLE PRECISION;
