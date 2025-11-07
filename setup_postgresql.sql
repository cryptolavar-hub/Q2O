-- PostgreSQL 18 Database Setup Script
-- Creates q2o database and q2o_user

-- Create database
CREATE DATABASE q2o;

-- Create user
CREATE USER q2o_user WITH PASSWORD 'Q2OPostgres2025!';

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE q2o TO q2o_user;

-- Connect to q2o database
\c q2o

-- Grant schema privileges (PostgreSQL 18 compatible)
GRANT ALL ON SCHEMA public TO q2o_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO q2o_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO q2o_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO q2o_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO q2o_user;

-- Success message
SELECT 'Database q2o and user q2o_user created successfully!' AS status;

