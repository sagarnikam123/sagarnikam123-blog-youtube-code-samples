-- Creates the least-privilege user that mysqld-exporter uses to scrape metrics.
-- Runs automatically on first container start (empty data dir) via
-- /docker-entrypoint-initdb.d. Must match the creds in docker-compose.yml.
CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'exporterpass' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
