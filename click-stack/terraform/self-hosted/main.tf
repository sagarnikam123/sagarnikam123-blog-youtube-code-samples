resource "clickhouse_clickstack_dashboard" "logs" {
  dashboard_json = jsonencode({
    name = var.dashboard_name

    tiles = [
      {
        name = "Log count over time by service"
        id   = "terraform-log-count"
        x    = 0
        y    = 0
        w    = 24
        h    = 11

        config = {
          name                        = "Logs over time"
          sourceId                    = var.logs_source_id
          displayType                 = "line"
          granularity                 = "auto"
          alignDateRangeToGranularity = true
          select = [
            {
              aggFn                = "count"
              aggCondition         = ""
              aggConditionLanguage = "lucene"
              valueExpression      = ""
            }
          ]
          where         = ""
          whereLanguage = "lucene"
          groupBy       = "ServiceName"
        }
      }
    ]

    filters    = []
    containers = []
  })

  team = var.team_id
}
