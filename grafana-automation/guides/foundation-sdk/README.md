# Grafana Foundation SDK Guide

Complete guide for using the Grafana Foundation SDK to generate dashboards and resources programmatically with type safety.

## Overview

The Grafana Foundation SDK provides type-safe code generation for Grafana dashboards and resources. It supports multiple programming languages and ensures your dashboards are valid and consistent.

### Key Benefits:
- **Type Safety**: Compile-time validation of dashboard structure
- **Code Generation**: Generate dashboards programmatically
- **Multi-Language**: Support for Go, TypeScript/JavaScript, Python
- **Version Control**: Dashboard definitions as code
- **Consistency**: Standardized dashboard patterns

## Installation

### Go
```bash
go get github.com/grafana/grafana-foundation-sdk/go
```

### TypeScript/JavaScript
```bash
npm install @grafana/foundation-sdk
```

### Python
```bash
pip install grafana-foundation-sdk
```

## Go Examples

### Basic Dashboard Creation
```go
package main

import (
    "encoding/json"
    "fmt"
    "github.com/grafana/grafana-foundation-sdk/go/dashboard"
    "github.com/grafana/grafana-foundation-sdk/go/stat"
    "github.com/grafana/grafana-foundation-sdk/go/prometheus"
)

func main() {
    // Create a stat panel
    panel := stat.NewPanelBuilder().
        Title("CPU Usage").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)").
                RefId("A").
                Build(),
        }).
        Build()

    // Create dashboard
    dash := dashboard.NewDashboardBuilder("System Metrics").
        Tags([]string{"system", "monitoring"}).
        Panel(panel).
        Time(dashboard.Time{
            From: "now-1h",
            To:   "now",
        }).
        Refresh("30s").
        Build()

    // Convert to JSON
    jsonData, _ := json.MarshalIndent(dash, "", "  ")
    fmt.Println(string(jsonData))
}
```

### Advanced Dashboard with Multiple Panels
```go
package main

import (
    "encoding/json"
    "fmt"
    "github.com/grafana/grafana-foundation-sdk/go/dashboard"
    "github.com/grafana/grafana-foundation-sdk/go/stat"
    "github.com/grafana/grafana-foundation-sdk/go/timeseries"
    "github.com/grafana/grafana-foundation-sdk/go/prometheus"
)

func main() {
    // CPU Usage Stat Panel
    cpuPanel := stat.NewPanelBuilder().
        Title("CPU Usage").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)").
                RefId("A").
                Build(),
        }).
        GridPos(dashboard.GridPos{H: 8, W: 6, X: 0, Y: 0}).
        Build()

    // Memory Usage Stat Panel
    memoryPanel := stat.NewPanelBuilder().
        Title("Memory Usage").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100").
                RefId("B").
                Build(),
        }).
        GridPos(dashboard.GridPos{H: 8, W: 6, X: 6, Y: 0}).
        Build()

    // CPU Usage Time Series
    cpuTimeSeriesPanel := timeseries.NewPanelBuilder().
        Title("CPU Usage Over Time").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)").
                RefId("C").
                LegendFormat("{{instance}}").
                Build(),
        }).
        GridPos(dashboard.GridPos{H: 8, W: 12, X: 0, Y: 8}).
        Build()

    // Create dashboard with template variables
    instanceVariable := dashboard.NewVariableBuilder().
        Name("instance").
        Type("query").
        Query(prometheus.NewVariableQueryBuilder().
            Query("label_values(up, instance)").
            Build()).
        Multi(true).
        IncludeAll(true).
        Build()

    dash := dashboard.NewDashboardBuilder("Advanced System Metrics").
        Tags([]string{"system", "monitoring", "advanced"}).
        Panel(cpuPanel).
        Panel(memoryPanel).
        Panel(cpuTimeSeriesPanel).
        Variable(instanceVariable).
        Time(dashboard.Time{
            From: "now-6h",
            To:   "now",
        }).
        Refresh("30s").
        Build()

    // Convert to JSON
    jsonData, _ := json.MarshalIndent(dash, "", "  ")
    fmt.Println(string(jsonData))
}
```

### Dashboard with Alerts
```go
package main

import (
    "encoding/json"
    "fmt"
    "github.com/grafana/grafana-foundation-sdk/go/dashboard"
    "github.com/grafana/grafana-foundation-sdk/go/stat"
    "github.com/grafana/grafana-foundation-sdk/go/prometheus"
    "github.com/grafana/grafana-foundation-sdk/go/alerting"
)

func main() {
    // Create panel with alert
    panel := stat.NewPanelBuilder().
        Title("CPU Usage with Alert").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)").
                RefId("A").
                Build(),
        }).
        Alert(alerting.NewAlertBuilder().
            Title("High CPU Usage").
            Message("CPU usage is above 80%").
            Frequency("10s").
            Conditions([]alerting.Condition{
                alerting.NewConditionBuilder().
                    Query("A", "5m", "now").
                    Reducer("avg").
                    Evaluator("gt", []float64{80}).
                    Build(),
            }).
            Build()).
        Build()

    dash := dashboard.NewDashboardBuilder("System Metrics with Alerts").
        Tags([]string{"system", "monitoring", "alerts"}).
        Panel(panel).
        Build()

    jsonData, _ := json.MarshalIndent(dash, "", "  ")
    fmt.Println(string(jsonData))
}
```

## TypeScript/JavaScript Examples

### Basic Dashboard Creation
```typescript
import { DashboardBuilder } from '@grafana/foundation-sdk/dashboard';
import { StatPanelBuilder } from '@grafana/foundation-sdk/stat';
import { PrometheusDataqueryBuilder } from '@grafana/foundation-sdk/prometheus';

// Create stat panel
const panel = new StatPanelBuilder()
  .title('CPU Usage')
  .unit('percent')
  .min(0)
  .max(100)
  .targets([
    new PrometheusDataqueryBuilder()
      .expr('100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
      .refId('A')
      .build()
  ])
  .build();

// Create dashboard
const dashboard = new DashboardBuilder('System Metrics')
  .tags(['system', 'monitoring'])
  .panel(panel)
  .time({
    from: 'now-1h',
    to: 'now'
  })
  .refresh('30s')
  .build();

console.log(JSON.stringify(dashboard, null, 2));
```

### Advanced Dashboard with Row Panels
```typescript
import { 
  DashboardBuilder, 
  RowPanelBuilder,
  GridPos 
} from '@grafana/foundation-sdk/dashboard';
import { StatPanelBuilder } from '@grafana/foundation-sdk/stat';
import { TimeseriesPanelBuilder } from '@grafana/foundation-sdk/timeseries';
import { PrometheusDataqueryBuilder } from '@grafana/foundation-sdk/prometheus';

// System Overview Row
const systemRow = new RowPanelBuilder()
  .title('System Overview')
  .gridPos(new GridPos(1, 24, 0, 0))
  .build();

// CPU Panel
const cpuPanel = new StatPanelBuilder()
  .title('CPU Usage')
  .unit('percent')
  .targets([
    new PrometheusDataqueryBuilder()
      .expr('100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
      .refId('A')
      .build()
  ])
  .gridPos(new GridPos(8, 6, 0, 1))
  .build();

// Memory Panel
const memoryPanel = new StatPanelBuilder()
  .title('Memory Usage')
  .unit('percent')
  .targets([
    new PrometheusDataqueryBuilder()
      .expr('(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100')
      .refId('B')
      .build()
  ])
  .gridPos(new GridPos(8, 6, 6, 1))
  .build();

// Network Row
const networkRow = new RowPanelBuilder()
  .title('Network')
  .gridPos(new GridPos(1, 24, 0, 9))
  .build();

// Network Traffic Panel
const networkPanel = new TimeseriesPanelBuilder()
  .title('Network Traffic')
  .unit('Bps')
  .targets([
    new PrometheusDataqueryBuilder()
      .expr('rate(node_network_receive_bytes_total[5m])')
      .refId('C')
      .legendFormat('{{device}} - Receive')
      .build(),
    new PrometheusDataqueryBuilder()
      .expr('rate(node_network_transmit_bytes_total[5m])')
      .refId('D')
      .legendFormat('{{device}} - Transmit')
      .build()
  ])
  .gridPos(new GridPos(8, 24, 0, 10))
  .build();

// Create dashboard
const dashboard = new DashboardBuilder('Comprehensive System Metrics')
  .tags(['system', 'monitoring', 'comprehensive'])
  .panel(systemRow)
  .panel(cpuPanel)
  .panel(memoryPanel)
  .panel(networkRow)
  .panel(networkPanel)
  .time({
    from: 'now-6h',
    to: 'now'
  })
  .refresh('30s')
  .build();

console.log(JSON.stringify(dashboard, null, 2));
```

### Dashboard with Template Variables
```typescript
import { 
  DashboardBuilder,
  VariableBuilder 
} from '@grafana/foundation-sdk/dashboard';
import { TimeseriesPanelBuilder } from '@grafana/foundation-sdk/timeseries';
import { PrometheusDataqueryBuilder, PrometheusVariableQueryBuilder } from '@grafana/foundation-sdk/prometheus';

// Create template variables
const instanceVariable = new VariableBuilder()
  .name('instance')
  .type('query')
  .query(
    new PrometheusVariableQueryBuilder()
      .query('label_values(up, instance)')
      .build()
  )
  .multi(true)
  .includeAll(true)
  .build();

const jobVariable = new VariableBuilder()
  .name('job')
  .type('query')
  .query(
    new PrometheusVariableQueryBuilder()
      .query('label_values(up, job)')
      .build()
  )
  .multi(false)
  .includeAll(false)
  .build();

// Create panel using variables
const panel = new TimeseriesPanelBuilder()
  .title('CPU Usage by Instance')
  .unit('percent')
  .targets([
    new PrometheusDataqueryBuilder()
      .expr('100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle", instance=~"$instance", job="$job"}[5m])) * 100)')
      .refId('A')
      .legendFormat('{{instance}}')
      .build()
  ])
  .build();

// Create dashboard
const dashboard = new DashboardBuilder('Templated System Metrics')
  .tags(['system', 'monitoring', 'templated'])
  .variable(instanceVariable)
  .variable(jobVariable)
  .panel(panel)
  .build();

console.log(JSON.stringify(dashboard, null, 2));
```

## Python Examples

### Basic Dashboard Creation
```python
from grafana_foundation_sdk.dashboard import DashboardBuilder
from grafana_foundation_sdk.stat import StatPanelBuilder
from grafana_foundation_sdk.prometheus import PrometheusDataqueryBuilder
import json

# Create stat panel
panel = (StatPanelBuilder()
    .title("CPU Usage")
    .unit("percent")
    .min(0)
    .max(100)
    .targets([
        PrometheusDataqueryBuilder()
            .expr("100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)")
            .ref_id("A")
            .build()
    ])
    .build())

# Create dashboard
dashboard = (DashboardBuilder("System Metrics")
    .tags(["system", "monitoring"])
    .panel(panel)
    .time({
        "from": "now-1h",
        "to": "now"
    })
    .refresh("30s")
    .build())

print(json.dumps(dashboard, indent=2))
```

### Advanced Dashboard with Custom Panels
```python
from grafana_foundation_sdk.dashboard import DashboardBuilder, GridPos
from grafana_foundation_sdk.stat import StatPanelBuilder
from grafana_foundation_sdk.timeseries import TimeseriesPanelBuilder
from grafana_foundation_sdk.table import TablePanelBuilder
from grafana_foundation_sdk.prometheus import PrometheusDataqueryBuilder
import json

# System metrics panels
cpu_panel = (StatPanelBuilder()
    .title("CPU Usage")
    .unit("percent")
    .targets([
        PrometheusDataqueryBuilder()
            .expr("100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)")
            .ref_id("A")
            .build()
    ])
    .grid_pos(GridPos(h=8, w=6, x=0, y=0))
    .build())

memory_panel = (StatPanelBuilder()
    .title("Memory Usage")
    .unit("percent")
    .targets([
        PrometheusDataqueryBuilder()
            .expr("(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100")
            .ref_id("B")
            .build()
    ])
    .grid_pos(GridPos(h=8, w=6, x=6, y=0))
    .build())

# Time series panel
cpu_timeseries = (TimeseriesPanelBuilder()
    .title("CPU Usage Over Time")
    .unit("percent")
    .targets([
        PrometheusDataqueryBuilder()
            .expr("100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)")
            .ref_id("C")
            .legend_format("{{instance}}")
            .build()
    ])
    .grid_pos(GridPos(h=8, w=12, x=0, y=8))
    .build())

# Table panel
process_table = (TablePanelBuilder()
    .title("Top Processes")
    .targets([
        PrometheusDataqueryBuilder()
            .expr("topk(10, rate(node_cpu_seconds_total{mode!=\"idle\"}[5m]))")
            .ref_id("D")
            .format("table")
            .build()
    ])
    .grid_pos(GridPos(h=8, w=12, x=12, y=8))
    .build())

# Create comprehensive dashboard
dashboard = (DashboardBuilder("Comprehensive System Dashboard")
    .tags(["system", "monitoring", "comprehensive"])
    .panel(cpu_panel)
    .panel(memory_panel)
    .panel(cpu_timeseries)
    .panel(process_table)
    .time({
        "from": "now-6h",
        "to": "now"
    })
    .refresh("30s")
    .build())

print(json.dumps(dashboard, indent=2))
```

### Dashboard Factory Pattern
```python
from grafana_foundation_sdk.dashboard import DashboardBuilder
from grafana_foundation_sdk.stat import StatPanelBuilder
from grafana_foundation_sdk.timeseries import TimeseriesPanelBuilder
from grafana_foundation_sdk.prometheus import PrometheusDataqueryBuilder
import json

class DashboardFactory:
    def __init__(self, datasource="Prometheus"):
        self.datasource = datasource
    
    def create_stat_panel(self, title, expr, unit="short", x=0, y=0, w=6, h=8):
        return (StatPanelBuilder()
            .title(title)
            .unit(unit)
            .targets([
                PrometheusDataqueryBuilder()
                    .expr(expr)
                    .ref_id("A")
                    .build()
            ])
            .grid_pos(GridPos(h=h, w=w, x=x, y=y))
            .build())
    
    def create_timeseries_panel(self, title, expr, unit="short", x=0, y=0, w=12, h=8):
        return (TimeseriesPanelBuilder()
            .title(title)
            .unit(unit)
            .targets([
                PrometheusDataqueryBuilder()
                    .expr(expr)
                    .ref_id("A")
                    .build()
            ])
            .grid_pos(GridPos(h=h, w=w, x=x, y=y))
            .build())
    
    def create_system_dashboard(self):
        panels = [
            self.create_stat_panel("CPU Usage", 
                "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)", 
                "percent", 0, 0),
            self.create_stat_panel("Memory Usage", 
                "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100", 
                "percent", 6, 0),
            self.create_stat_panel("Disk Usage", 
                "(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100", 
                "percent", 12, 0),
            self.create_timeseries_panel("Network Traffic", 
                "rate(node_network_receive_bytes_total[5m])", 
                "Bps", 0, 8)
        ]
        
        dashboard = DashboardBuilder("System Overview")
        for panel in panels:
            dashboard.panel(panel)
        
        return (dashboard
            .tags(["system", "monitoring"])
            .time({"from": "now-1h", "to": "now"})
            .refresh("30s")
            .build())

# Usage
factory = DashboardFactory()
dashboard = factory.create_system_dashboard()
print(json.dumps(dashboard, indent=2))
```

## Best Practices

### 1. Code Organization
```
dashboards/
├── builders/
│   ├── system_dashboard.go
│   ├── application_dashboard.go
│   └── business_dashboard.go
├── panels/
│   ├── common_panels.go
│   └── custom_panels.go
├── variables/
│   └── template_variables.go
└── main.go
```

### 2. Reusable Components
```go
// common_panels.go
package panels

import (
    "github.com/grafana/grafana-foundation-sdk/go/dashboard"
    "github.com/grafana/grafana-foundation-sdk/go/stat"
    "github.com/grafana/grafana-foundation-sdk/go/prometheus"
)

func CPUUsagePanel(x, y int) dashboard.Panel {
    return stat.NewPanelBuilder().
        Title("CPU Usage").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)").
                RefId("A").
                Build(),
        }).
        GridPos(dashboard.GridPos{H: 8, W: 6, X: x, Y: y}).
        Build()
}

func MemoryUsagePanel(x, y int) dashboard.Panel {
    return stat.NewPanelBuilder().
        Title("Memory Usage").
        Unit("percent").
        Min(0).
        Max(100).
        Targets([]dashboard.Target{
            prometheus.NewDataqueryBuilder().
                Expr("(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100").
                RefId("A").
                Build(),
        }).
        GridPos(dashboard.GridPos{H: 8, W: 6, X: x, Y: y}).
        Build()
}
```

### 3. Configuration-Driven Dashboards
```typescript
interface DashboardConfig {
  title: string;
  tags: string[];
  panels: PanelConfig[];
  variables?: VariableConfig[];
}

interface PanelConfig {
  type: 'stat' | 'timeseries' | 'table';
  title: string;
  targets: TargetConfig[];
  gridPos: GridPos;
}

function createDashboardFromConfig(config: DashboardConfig): Dashboard {
  const builder = new DashboardBuilder(config.title)
    .tags(config.tags);

  // Add variables
  if (config.variables) {
    config.variables.forEach(variable => {
      builder.variable(createVariable(variable));
    });
  }

  // Add panels
  config.panels.forEach(panelConfig => {
    builder.panel(createPanel(panelConfig));
  });

  return builder.build();
}
```

### 4. Testing
```go
func TestDashboardGeneration(t *testing.T) {
    dash := dashboard.NewDashboardBuilder("Test Dashboard").
        Tags([]string{"test"}).
        Build()

    // Validate dashboard structure
    assert.Equal(t, "Test Dashboard", dash.Title)
    assert.Contains(t, dash.Tags, "test")
    
    // Validate JSON serialization
    jsonData, err := json.Marshal(dash)
    assert.NoError(t, err)
    assert.NotEmpty(t, jsonData)
}
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Generate Dashboards
on:
  push:
    paths: ['dashboards/**']

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Go
        uses: actions/setup-go@v3
        with:
          go-version: '1.21'
      
      - name: Generate Dashboards
        run: |
          cd dashboards
          go run main.go > ../generated-dashboards.json
      
      - name: Deploy to Grafana
        env:
          GRAFANA_URL: ${{ secrets.GRAFANA_URL }}
          GRAFANA_TOKEN: ${{ secrets.GRAFANA_TOKEN }}
        run: |
          curl -X POST "$GRAFANA_URL/api/dashboards/db" \
            -H "Authorization: Bearer $GRAFANA_TOKEN" \
            -H "Content-Type: application/json" \
            -d @generated-dashboards.json
```

## References

- [Grafana Foundation SDK Documentation](https://grafana.com/docs/grafana/latest/observability-as-code/foundation-sdk/)
- [GitHub Repository](https://github.com/grafana/grafana-foundation-sdk)
- [Dashboard Automation Guide](https://grafana.com/docs/grafana/latest/observability-as-code/foundation-sdk/dashboard-automation/)
- [API Reference](https://grafana.com/docs/grafana/latest/observability-as-code/foundation-sdk/api-reference/)