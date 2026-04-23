# Prometheus Instrumentation for RAPai Ontology

## Overview

The `ontology/metrics.py` module provides comprehensive Prometheus instrumentation for the RAPai Ontology system, enabling real-time monitoring of performance, reliability, and operational health.

**Status:** Phase II, Week 11 — Metrics Infrastructure Foundation

**All metrics are exposed in Prometheus text exposition format** and can be consumed by Prometheus, Grafana, Datadog, or other observability platforms.

## SLO Targets (Phase II+)

| Metric | SLO Target | Business Impact |
|--------|-----------|-----------------|
| Roundtrip validation P99 | < 1.0ms | Ensures fast schema enforcement |
| Rule execution P99 | < 0.1ms | Prevents constraint bottlenecks |
| Cache hit ratio | > 70% | Reduces downstream agent latency |
| Action execution P99 | < 100ms | Maintains user-facing responsiveness |
| WorkLog parsing throughput | > 1000 logs/min | Supports batch ingestion |

## Metric Categories

### 1. Latency Metrics (Histograms)

Track operation execution time with configurable buckets for SLO monitoring.

#### `ontology_validation_latency_ms`
Pydantic validation latency (JSON → model roundtrip)

- **Labels:** `object_type` (Project, Task, WorkLog, Person, Event, etc.)
- **Buckets:** 0.1, 0.5, 1.0, 2.0, 5.0, 10.0 ms
- **SLO:** P99 < 1.0ms
- **Business meaning:** Measures schema enforcement cost; spike indicates model complexity increase

```python
from ontology.metrics import ontology_validation_latency_ms, record_validation_latency

# Record latency
record_validation_latency("Project", 0.45)

# Or direct recording
ontology_validation_latency_ms.labels(object_type="Task").observe(0.32)
```

#### `ontology_rule_execution_ms`
Individual constraint rule evaluation latency

- **Labels:** `rule_id` (e.g., RULE-001-TRL-GATE), `object_type`
- **Buckets:** 0.01, 0.05, 0.1, 0.5, 1.0 ms
- **SLO:** P99 < 0.1ms
- **Business meaning:** Identifies slow rules; spike indicates N+1 evaluation or expensive constraint

```python
from ontology.metrics import record_rule_execution

record_rule_execution(
    rule_id="RULE-001-TRL-GATE",
    object_type="Project",
    latency_ms=0.045
)
```

#### `action_execution_time_ms`
Domain action execution latency (CreateTask, AssignPerson, etc.)

- **Labels:** `action_type`, `autonomy_level` (autonomous, human_approved, human_directed)
- **Buckets:** 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0 ms
- **SLO:** P99 < 100ms
- **Business meaning:** Tracks domain operation performance; high latency on autonomous actions may indicate rule violations or decision delays

```python
from ontology.metrics import action_execution_time_ms

action_execution_time_ms.labels(
    action_type="CreateTask",
    autonomy_level="autonomous"
).observe(12.5)
```

#### `db_query_latency_ms`
Database operation execution latency (PostgreSQL)

- **Labels:** `query_type` (select, insert, update, delete, transaction)
- **Buckets:** 0.1, 1.0, 5.0, 10.0, 50.0, 100.0 ms
- **Business meaning:** Identifies slow queries; spike indicates slow query or missing index

### 2. Throughput Metrics (Counters)

Track operation volume and success rates.

#### `worklog_parse_total`
WorkLog parsing operation count

- **Labels:** `status` (success, failure, malformed_json)
- **Business meaning:** Monitors ingestion reliability; failure spike indicates data quality issue or schema drift

```python
from ontology.metrics import record_worklog_parse

record_worklog_parse("success")
record_worklog_parse("failure")
```

#### `action_execution_total`
Action execution count

- **Labels:** `action_type`, `status` (success, validation_error, rule_violation, unknown_error)
- **Business meaning:** Measures governance operation throughput; error rate indicates rule design issues or data inconsistency

```python
from ontology.metrics import action_execution_total

action_execution_total.labels(
    action_type="CreateTask",
    status="success"
).inc()
```

#### `decision_created_total` (KPI Metric)
Decision object creation count

- **Labels:** `decision_type` (gate_decision, trade_off, risk_mitigation, etc.)
- **Business meaning:** Measures decision-making volume across RAPai; low volume may indicate bottleneck

```python
from ontology.metrics import record_decision_creation

record_decision_creation("gate_decision")
```

### 3. Cache Metrics (Gauges)

Monitor system cache health and object counts.

#### `ontology_cache_hit_ratio`
Cache hit ratio [0.0-1.0 scale]

- **SLO:** > 0.70 (70%)
- **Business meaning:** Higher ratio reduces downstream latency; trends > 0.90 indicate hot working set

```python
from ontology.metrics import update_cache_hit_ratio

update_cache_hit_ratio(0.82)
```

#### `ontology_object_count`
Total object count by type in system

- **Labels:** `object_type`
- **Business meaning:** Monitors system growth; steep increase may trigger optimization

```python
from ontology.metrics import update_object_count

update_object_count("Project", 1250)
update_object_count("Task", 5600)
```

### 4. Quality Metrics (Gauges)

Monitor data quality and governance health.

#### `ontology_error_rate`
Current error rate [0.0-1.0 scale] (rolling 5-min window)

- **Alert threshold:** > 0.05 (5%)
- **Business meaning:** Indicates data quality or schema health; trend > 0.05 warrants investigation

```python
from ontology.metrics import update_error_rate

update_error_rate(0.02)
```

#### `compliance_violation_count`
Compliance violations by validator type

- **Labels:** `validator_type` (trl_gate, crl_gate, wbs_validity, cardinality, self_reference, etc.)
- **Business meaning:** Should trend toward 0; each violation represents rejected invalid action

```python
from ontology.metrics import record_compliance_violation

record_compliance_violation("trl_gate")
record_compliance_violation("wbs_validity")
```

### 5. Database Metrics

#### `db_connection_pool_usage`
Database connection pool utilization [0.0-1.0]

- **Alert threshold:** > 0.85 (connection exhaustion risk)
- **Business meaning:** Tracks database connection pressure; high utilization indicates need for tuning or optimization

```python
from ontology.metrics import update_connection_pool_usage

update_connection_pool_usage(0.65)
```

## Integration Patterns

### Pattern 1: Decorator-based Latency Tracking

Use `@track_latency()` for automatic instrumentation of validation functions:

```python
from ontology.metrics import track_latency, ontology_validation_latency_ms

@track_latency(
    ontology_validation_latency_ms,
    label_values={"object_type": "Project"}
)
def validate_project(project_dict: dict) -> bool:
    return "project_id" in project_dict and "name" in project_dict
```

### Pattern 2: Context Manager Instrumentation

Use `MetricsContext` when decorators are impractical (e.g., in __init__ methods):

```python
from ontology.metrics import MetricsContext, ontology_validation_latency_ms

def __init__(self, data: dict):
    with MetricsContext(
        histogram=ontology_validation_latency_ms,
        labels={"object_type": "Task"}
    ):
        self.validate(data)
```

### Pattern 3: Manual Recording

For fine-grained control, call recorder functions directly:

```python
from ontology.metrics import record_action_execution

start = time.perf_counter()
try:
    # Execute action
    create_task(task_data)
    status = "success"
except ValidationError:
    status = "validation_error"
finally:
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_action_execution(
        action_type="CreateTask",
        autonomy_level="autonomous",
        latency_ms=elapsed_ms,
        status=status
    )
```

### Pattern 4: Full Integration Workflow

Combining validation → rules → action execution:

```python
from ontology.metrics import (
    MetricsContext,
    ontology_validation_latency_ms,
    record_rule_execution,
    record_action_execution
)

# Step 1: Validate input
with MetricsContext(
    histogram=ontology_validation_latency_ms,
    labels={"object_type": "Project"}
):
    is_valid = validate_schema(data)

# Step 2: Evaluate rules
for rule_id, rule_fn in rules.items():
    start = time.perf_counter()
    passed = rule_fn(data)
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_rule_execution(rule_id, "Project", elapsed_ms)

# Step 3: Execute action
start = time.perf_counter()
try:
    execute_action(data)
    status = "success"
except Exception as e:
    status = "failure"
finally:
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_action_execution("CreateProject", "autonomous", elapsed_ms, status)
```

## Exposing Metrics

### Option 1: Built-in HTTP Server (Development)

```python
from ontology.metrics import bootstrap_metrics_server

# Start metrics HTTP server on port 8000
bootstrap_metrics_server(host="localhost", port=8000)

# Metrics available at: http://localhost:8000/metrics
```

### Option 2: Manual Export

```python
from ontology.metrics import get_metrics_content

# Get Prometheus text format export
metrics_text = get_metrics_content()
print(metrics_text.decode())
```

### Option 3: Integration with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import Response
from ontology.metrics import get_metrics_content, CONTENT_TYPE_LATEST

app = FastAPI()

@app.get("/metrics")
def metrics():
    return Response(get_metrics_content(), media_type=CONTENT_TYPE_LATEST)
```

### Option 4: Integration with Flask

```python
from flask import Flask, Response
from ontology.metrics import get_metrics_content
from prometheus_client import CONTENT_TYPE_LATEST

app = Flask(__name__)

@app.route("/metrics")
def metrics():
    return Response(get_metrics_content(), mimetype=CONTENT_TYPE_LATEST)
```

## Example: Full Integration

See `ontology/examples_metrics_integration.py` for complete working examples:

```bash
# Run examples
python -m ontology.examples_metrics_integration
```

## Testing

37 unit tests verify metrics functionality:

```bash
# Run metrics tests
pytest ontology/tests/unit/test_metrics.py -v

# With coverage
pytest ontology/tests/unit/test_metrics.py --cov=ontology.metrics --cov-report=html
```

**Test coverage:** 99% (118/118 statements)

## Prometheus Queries

### Sample Queries for Monitoring

```promql
# P99 validation latency (SLO: < 1.0ms)
histogram_quantile(0.99, ontology_validation_latency_ms)

# Rule execution error rate
rate(ontology_rule_execution_ms_count[5m])

# Cache hit ratio trend
avg(ontology_cache_hit_ratio)

# Action execution success rate
sum(rate(action_execution_total{status="success"}[5m])) /
sum(rate(action_execution_total[5m]))

# Compliance violations by type
sum(compliance_violation_count) by (validator_type)

# Database query latency P50/P95/P99
histogram_quantile(0.50, db_query_latency_ms)
histogram_quantile(0.95, db_query_latency_ms)
histogram_quantile(0.99, db_query_latency_ms)
```

## Alert Rules (Example)

```yaml
groups:
  - name: ontology
    interval: 30s
    rules:
      - alert: ValidationLatencyHigh
        expr: histogram_quantile(0.99, ontology_validation_latency_ms) > 1.0
        for: 5m
        annotations:
          summary: "Validation P99 latency exceeds SLO"

      - alert: CacheHitRatioBelowSLO
        expr: ontology_cache_hit_ratio < 0.70
        for: 10m
        annotations:
          summary: "Cache hit ratio below 70% SLO"

      - alert: ComplianceViolationSpike
        expr: increase(compliance_violation_count[5m]) > 10
        for: 5m
        annotations:
          summary: "Spike in compliance violations detected"

      - alert: ActionExecutionErrorRateHigh
        expr: |
          sum(rate(action_execution_total{status!="success"}[5m])) /
          sum(rate(action_execution_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "Action execution error rate > 5%"
```

## Grafana Dashboard

Example dashboard JSON (save as `grafana-ontology-dashboard.json`):

```json
{
  "dashboard": {
    "title": "RAPai Ontology Metrics",
    "panels": [
      {
        "title": "Validation Latency P99",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, ontology_validation_latency_ms)"
          }
        ]
      },
      {
        "title": "Cache Hit Ratio",
        "targets": [
          {
            "expr": "ontology_cache_hit_ratio"
          }
        ]
      },
      {
        "title": "Compliance Violations",
        "targets": [
          {
            "expr": "sum(compliance_violation_count) by (validator_type)"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Metrics Not Appearing

1. Verify `prometheus-client` is installed:
   ```bash
   pip install "prometheus-client>=0.20,<1"
   ```

2. Check metrics are being recorded:
   ```python
   from ontology.metrics import get_metrics_content
   content = get_metrics_content()
   assert b"ontology_validation_latency_ms" in content
   ```

### High Latency Spikes

1. Check for slow rules: Filter by `rule_id` in `ontology_rule_execution_ms`
2. Identify expensive validations: Check `ontology_validation_latency_ms` by `object_type`
3. Monitor action execution: Look for specific `action_type` + `autonomy_level` combinations

### Cache Hit Ratio Below SLO

1. Review cache invalidation frequency
2. Check working set size vs. cache capacity
3. Analyze cache key design (too granular?)
4. Consider increasing cache TTL or size

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [prometheus-client Python](https://github.com/prometheus/client_python)
- [OpenTelemetry Best Practices](https://opentelemetry.io/)
- `ontology/metrics.py` — Source code with detailed docstrings
- `ontology/tests/unit/test_metrics.py` — Unit tests and integration examples
