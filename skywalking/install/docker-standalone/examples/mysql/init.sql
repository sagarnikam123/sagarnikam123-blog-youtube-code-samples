-- =============================================================================
-- MySQL Exporter User Setup
-- =============================================================================
-- This script creates the necessary user and grants for mysqld_exporter
-- =============================================================================

-- Create exporter user with required privileges
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'exporterpassword';

-- Grant necessary privileges for monitoring
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Create sample data for testing
CREATE DATABASE IF NOT EXISTS testdb;
USE testdb;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Wilson', 'bob@example.com');
