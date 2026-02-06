#!/bin/bash
# =============================================================================
# Enable Database Monitoring for SkyWalking
# =============================================================================
# Usage:
#   ./enable-database-monitoring.sh <database> [options]
#
# Examples:
#   ./enable-database-monitoring.sh all
#   ./enable-database-monitoring.sh mysql --host mysql-service --port 3306
#   ./enable-database-monitoring.sh postgresql
#   ./enable-database-monitoring.sh redis --host redis-master
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/../base/database-monitoring"
NAMESPACE="${NAMESPACE:-skywalking}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_usage() {
    echo "Usage: $0 <database> [options]"
    echo ""
    echo "Databases:"
    echo "  all           Show all database configurations"
    echo "  mysql         MySQL/MariaDB exporter"
    echo "  postgresql    PostgreSQL exporter"
    echo "  redis         Redis exporter"
    echo "  elasticsearch Elasticsearch exporter"
    echo "  mongodb       MongoDB exporter"
    echo "  bookkeeper    BookKeeper configuration"
    echo "  clickhouse    ClickHouse exporter"
    echo ""
    echo "Options:"
    echo "  --host        Database host (default: <db>-service)"
    echo "  --port        Database port"
    echo "  --namespace   Kubernetes namespace (default: skywalking)"
}

show_mysql_config() {
    echo -e "${GREEN}MySQL/MariaDB Monitoring${NC}"
    echo "========================="
    echo ""
    echo "1. Create monitoring user in MySQL:"
    echo "   CREATE USER 'exporter'@'%' IDENTIFIED BY 'your-password';"
    echo "   GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';"
    echo "   FLUSH PRIVILEGES;"
    echo ""
    echo "2. Update secret in mysql-exporter.yaml:"
    echo "   DATA_SOURCE_NAME: \"exporter:your-password@tcp(${DB_HOST:-mysql-service}:${DB_PORT:-3306})/\""
    echo ""
    echo "3. Deploy exporter:"
    echo "   kubectl apply -f ${BASE_DIR}/mysql-exporter.yaml -n ${NAMESPACE}"
    echo ""
    echo "4. Add OAP rule: mysql (or mariadb)"
    echo "   SW_OTEL_RECEIVER_ENABLED_OC_RULES: \"...,mysql,...\""
}

show_postgresql_config() {
    echo -e "${GREEN}PostgreSQL Monitoring${NC}"
    echo "======================"
    echo ""
    echo "1. Create monitoring user in PostgreSQL:"
    echo "   CREATE USER exporter WITH PASSWORD 'your-password';"
    echo "   GRANT pg_monitor TO exporter;"
    echo ""
    echo "2. Update secret in postgresql-exporter.yaml:"
    echo "   DATA_SOURCE_NAME: \"postgresql://exporter:your-password@${DB_HOST:-postgresql-service}:${DB_PORT:-5432}/postgres?sslmode=disable\""
    echo ""
    echo "3. Deploy exporter:"
    echo "   kubectl apply -f ${BASE_DIR}/postgresql-exporter.yaml -n ${NAMESPACE}"
    echo ""
    echo "4. Add OAP rule: postgresql"
}

show_redis_config() {
    echo -e "${GREEN}Redis Monitoring${NC}"
    echo "================="
    echo ""
    echo "1. Update redis-exporter.yaml with your Redis address:"
    echo "   REDIS_ADDR: \"redis://${DB_HOST:-redis-service}:${DB_PORT:-6379}\""
    echo ""
    echo "2. If Redis has password, update secret:"
    echo "   REDIS_PASSWORD: \"your-redis-password\""
    echo ""
    echo "3. Deploy exporter:"
    echo "   kubectl apply -f ${BASE_DIR}/redis-exporter.yaml -n ${NAMESPACE}"
    echo ""
    echo "4. Add OAP rule: redis"
}

show_elasticsearch_config() {
    echo -e "${GREEN}Elasticsearch Monitoring${NC}"
    echo "========================="
    echo ""
    echo "1. Update elasticsearch-exporter.yaml with your ES URI:"
    echo "   --es.uri=http://${DB_HOST:-elasticsearch-service}:${DB_PORT:-9200}"
    echo ""
    echo "2. If security enabled, update secret:"
    echo "   ES_USERNAME: \"elastic\""
    echo "   ES_PASSWORD: \"your-password\""
    echo ""
    echo "3. Deploy exporter:"
    echo "   kubectl apply -f ${BASE_DIR}/elasticsearch-exporter.yaml -n ${NAMESPACE}"
    echo ""
    echo "4. Add OAP rule: elasticsearch"
}

show_mongodb_config() {
    echo -e "${GREEN}MongoDB Monitoring${NC}"
    echo "==================="
    echo ""
    echo "1. Create monitoring user in MongoDB:"
    echo "   use admin"
    echo "   db.createUser({"
    echo "     user: 'exporter',"
    echo "     pwd: 'your-password',"
    echo "     roles: [{ role: 'clusterMonitor', db: 'admin' }]"
    echo "   })"
    echo ""
    echo "2. Update secret in mongodb-exporter.yaml:"
    echo "   MONGODB_URI: \"mongodb://exporter:your-password@${DB_HOST:-mongodb-service}:${DB_PORT:-27017}/admin\""
    echo ""
    echo "3. Deploy exporter:"
    echo "   kubectl apply -f ${BASE_DIR}/mongodb-exporter.yaml -n ${NAMESPACE}"
    echo ""
    echo "4. Add OAP rule: mongodb"
}

show_bookkeeper_config() {
    echo -e "${GREEN}BookKeeper Monitoring${NC}"
    echo "======================"
    echo ""
    echo "BookKeeper has built-in Prometheus metrics support."
    echo ""
    echo "1. Enable in BookKeeper config (bk_server.conf):"
    echo "   enableStatistics=true"
    echo "   statsProviderClass=org.apache.bookkeeper.stats.prometheus.PrometheusMetricsProvider"
    echo "   prometheusStatsHttpPort=8000"
    echo ""
    echo "2. Expose metrics service:"
    echo "   kubectl apply -f ${BASE_DIR}/bookkeeper-config.yaml -n ${NAMESPACE}"
    echo ""
    echo "3. Add OAP rule: bookkeeper"
}

show_clickhouse_config() {
    echo -e "${GREEN}ClickHouse Monitoring${NC}"
    echo "======================"
    echo ""
    echo "1. Update clickhouse-exporter.yaml with your ClickHouse URI:"
    echo "   -scrape_uri=http://${DB_HOST:-clickhouse-service}:${DB_PORT:-8123}/"
    echo ""
    echo "2. If authentication enabled, update secret:"
    echo "   CLICKHOUSE_USER: \"default\""
    echo "   CLICKHOUSE_PASSWORD: \"your-password\""
    echo ""
    echo "3. Deploy exporter:"
    echo "   kubectl apply -f ${BASE_DIR}/clickhouse-exporter.yaml -n ${NAMESPACE}"
    echo ""
    echo "4. Add OAP rule: clickhouse"
}

show_all() {
    echo -e "${YELLOW}Database Monitoring Configuration${NC}"
    echo "==================================="
    echo ""
    show_mysql_config
    echo ""
    echo "---"
    echo ""
    show_postgresql_config
    echo ""
    echo "---"
    echo ""
    show_redis_config
    echo ""
    echo "---"
    echo ""
    show_elasticsearch_config
    echo ""
    echo "---"
    echo ""
    show_mongodb_config
    echo ""
    echo "---"
    echo ""
    show_bookkeeper_config
    echo ""
    echo "---"
    echo ""
    show_clickhouse_config
    echo ""
    echo -e "${YELLOW}OTel Collector Configuration${NC}"
    echo "============================="
    echo "Add scrape configs from: ${BASE_DIR}/otel-collector-database.yaml"
    echo ""
    echo -e "${YELLOW}Required OAP Rules${NC}"
    echo "==================="
    echo "SW_OTEL_RECEIVER_ENABLED_OC_RULES: \"oap,mysql,postgresql,redis,elasticsearch,mongodb,bookkeeper,clickhouse,...\""
}

# Parse arguments
DB_HOST=""
DB_PORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --host) DB_HOST="$2"; shift 2 ;;
        --port) DB_PORT="$2"; shift 2 ;;
        --namespace) NAMESPACE="$2"; shift 2 ;;
        -h|--help) print_usage; exit 0 ;;
        all) show_all; exit 0 ;;
        mysql) show_mysql_config; exit 0 ;;
        postgresql) show_postgresql_config; exit 0 ;;
        redis) show_redis_config; exit 0 ;;
        elasticsearch) show_elasticsearch_config; exit 0 ;;
        mongodb) show_mongodb_config; exit 0 ;;
        bookkeeper) show_bookkeeper_config; exit 0 ;;
        clickhouse) show_clickhouse_config; exit 0 ;;
        *) echo "Unknown option: $1"; print_usage; exit 1 ;;
    esac
done

print_usage
