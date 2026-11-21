terraform {
  required_version = ">= 1.5.0"

  required_providers {
    clickhouse = {
      source  = "ClickHouse/clickhouse"
      version = "= 3.25.0"
    }
  }
}
