-- Creates the least-privilege role that postgres-exporter uses to scrape metrics.
-- Runs automatically on first container start (empty data dir) via
-- /docker-entrypoint-initdb.d. Must match the DATA_SOURCE_NAME in docker-compose.yml.
-- pg_monitor (built-in since PG 10) grants read access to monitoring views/functions.
CREATE ROLE exporter WITH LOGIN PASSWORD 'exporterpass';
GRANT pg_monitor TO exporter;
