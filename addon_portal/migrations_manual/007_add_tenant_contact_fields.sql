-- Migration 007: Add contact fields to tenants table for OTP delivery
-- Date: 2025-11-14
-- Description: Adds email, phone_number, and otp_delivery_method fields to support OTP-based authentication

-- Add email field (nullable, for OTP delivery via email)
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS email VARCHAR(255) NULL;

-- Add phone_number field (nullable, for OTP delivery via SMS/WhatsApp)
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50) NULL;

-- Add otp_delivery_method field (default: 'email')
-- Options: 'email', 'sms', 'whatsapp', 'both'
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS otp_delivery_method VARCHAR(20) NOT NULL DEFAULT 'email';

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email) WHERE email IS NOT NULL;

-- Create index on phone_number for faster lookups
CREATE INDEX IF NOT EXISTS idx_tenants_phone ON tenants(phone_number) WHERE phone_number IS NOT NULL;

-- Add comment to document the fields
COMMENT ON COLUMN tenants.email IS 'Primary email address for OTP delivery and notifications';
COMMENT ON COLUMN tenants.phone_number IS 'Phone number for SMS/WhatsApp OTP delivery';
COMMENT ON COLUMN tenants.otp_delivery_method IS 'OTP delivery preference: email, sms, whatsapp, or both';

