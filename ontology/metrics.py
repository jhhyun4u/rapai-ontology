"""Prometheus instrumentation for RAPai Ontology.

This module provides comprehensive metrics collection for the ontology system,
enabling monitoring of performance, reliability, and operational health.

SLO Targets (Phase II+):
- Roundtrip validation (JSON ↔ Pydantic ↔ JSON): P99 < 1.0ms
- Rule execution: P99 < 0.1ms
- Cache hit ratio: > 70%
- Action execution: P99 < 100ms
- WorkLog parsing: > 1000 logs/min sustained

Business metrics tied to RAPai governance:
- Compliance violations: Should trend toward 0
- Cache hit ratio: Drives downstream agent responsiveness
- Decision creation: Tracks decision-making volume (KPI)
- TRL/CRL transitions: Tracks progress through governance gates

Metrics are exposed on port 8000 via Prometheus client library.
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any, Literal, TypeVar

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Context variables for tracking active spans
# ────────────────────────────────────────────────────────────────────────────

_metric_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "metric_context",
    default=None,
)


# ────────────────────────────────────────────────────────────────────────────
# Latency Metrics (Histograms)
# ────────────────────────────────────────────────────────────────────────────

ontology_validation_latency_ms = Histogram(
    name="ontology_validation_latency_ms",
    documentation="Pydantic validation latency (JSON→model). SLO: P99 < 1.0ms. "
    "Measures roundtrip equivalence enforcement cost.",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    labelnames=["object_type"],
)
"""Latency of Pydantic validation operations.

Labels:
- object_type: Core object being validated (Project, Task, WorkLog, Person, Event)

Business meaning: Low latency indicates fast validation; P99 spike indicates
model complexity increase or bottleneck in field validators.
"""

ontology_rule_execution_ms = Histogram(
    name="ontology_rule_execution_ms",
    documentation="Rule engine execution latency. SLO: P99 < 0.1ms. "
    "Includes SBVR rule lookup + constraint evaluation.",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
    labelnames=["rule_id", "object_type"],
)
"""Latency of individual rule executions.

Labels:
- rule_id: Unique constraint rule identifier
- object_type: Object being validated

Business meaning: Rule catalog performance; spike indicates N+1 rule evaluation
or expensive constraint check.
"""

action_execution_time_ms = Histogram(
    name="action_execution_time_ms",
    documentation="Agent action execution latency (e.g., create_task, assign_person). "
    "SLO: P99 < 100ms. Excludes LLM inference.",
    buckets=(1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0),
    labelnames=["action_type", "autonomy_level"],
)
"""Latency of domain action execution.

Labels:
- action_type: Action class (CreateTask, AssignPerson, LogWork, RecordDecision, etc.)
- autonomy_level: Execution context (autonomous, human_approved, human_directed)

Business meaning: Tracks domain operation performance; high latency on
autonomous actions may indicate constraint violations or decision delays.
"""

db_query_latency_ms = Histogram(
    name="db_query_latency_ms",
    documentation="Database query execution latency (PostgreSQL). "
    "Excludes network round-trip (phase III).",
    buckets=(0.1, 1.0, 5.0, 10.0, 50.0, 100.0),
    labelnames=["query_type"],
)
"""Latency of database operations.

Labels:
- query_type: select, insert, update, delete, transaction

Business meaning: Tracks persistent storage performance; spike indicates
slow query or missing index.
"""

# ────────────────────────────────────────────────────────────────────────────
# Throughput Metrics (Counters)
# ────────────────────────────────────────────────────────────────────────────

worklog_parse_total = Counter(
    name="worklog_parse_total",
    documentation="Total WorkLog parsing operations. Tracks batch volume "
    "and success rate (target: >99.9% success).",
    labelnames=["status"],
)
"""Count of WorkLog parsing attempts.

Labels:
- status: success, failure (validation error), malformed_json

Business meaning: Monitors WorkLog ingestion reliability; failure spike
indicates data quality issue or schema drift.
"""

action_execution_total = Counter(
    name="action_execution_total",
    documentation="Total action executions. Tracks domain operation volume "
    "and error rate per action type.",
    labelnames=["action_type", "status"],
)
"""Count of action executions.

Labels:
- action_type: Action class name
- status: success, validation_error, rule_violation, unknown_error

Business meaning: Measures governance operation throughput; error rate
indicates rule design issues or data inconsistency.
"""

decision_created_total = Counter(
    name="decision_created_total",
    documentation="Total Decision objects created. KPI metric tracking "
    "decision-making volume across RAPai.",
    labelnames=["decision_type"],
)
"""Count of Decision creations (KPI metric).

Labels:
- decision_type: Category of decision (gate_decision, trade_off, risk_mitigation, etc.)

Business meaning: Measures governance adoption; low volume may indicate
bottleneck in decision-making flow.
"""

# ────────────────────────────────────────────────────────────────────────────
# Cache Metrics (Gauges)
# ────────────────────────────────────────────────────────────────────────────

ontology_cache_hit_ratio = Gauge(
    name="ontology_cache_hit_ratio",
    documentation="Cache hit ratio [0.0-1.0]. SLO: > 0.70 (70%). "
    "Reflects Redis caching of Project/Task lookups.",
)
"""Cache hit ratio (0-1 scale).

Business meaning: Higher ratio reduces downstream latency (agent responsiveness);
target >70% to offset cache invalidation cost. Trends > 0.90 indicate hot working set.
"""

ontology_object_count = Gauge(
    name="ontology_object_count",
    documentation="Total object count in system by type. "
    "Tracks data volume for capacity planning.",
    labelnames=["object_type"],
)
"""In-memory or cached object counts by type.

Labels:
- object_type: Core or extended object type

Business meaning: Monitors system growth; steep increase may trigger
caching or query optimization.
"""

# ────────────────────────────────────────────────────────────────────────────
# Quality Metrics (Gauges)
# ────────────────────────────────────────────────────────────────────────────

ontology_error_rate = Gauge(
    name="ontology_error_rate",
    documentation="Current error rate [0.0-1.0] (rolling 5-min window). "
    "Combines validation errors, rule violations, and action failures.",
)
"""Current error rate (0-1 scale).

Business meaning: Indicates data quality or schema health; trend >0.05
warrants investigation.
"""

compliance_violation_count = Gauge(
    name="compliance_violation_count",
    documentation="Total compliance violations detected by type. "
    "Should trend toward 0; spike indicates rule design issue or data corruption.",
    labelnames=["validator_type"],
)
"""Count of violations by validator type.

Labels:
- validator_type: trl_gate, crl_gate, wbs_validity, cardinality, self_reference,
  contract_research_modality, identifier_format, enum_match, etc.

Business meaning: Tracks ontology governance health; each violation represents
rejected invalid action.
"""

# ────────────────────────────────────────────────────────────────────────────
# Database & Connection Metrics (Histograms + Gauges)
# ────────────────────────────────────────────────────────────────────────────

db_connection_pool_usage = Gauge(
    name="db_connection_pool_usage",
    documentation="Database connection pool utilization [0.0-1.0]. "
    "Alert if >0.85 (connection exhaustion risk).",
)
"""Connection pool usage (0-1 scale).

Business meaning: Tracks database connection pressure; high utilization
indicates need for connection pooling tuning or query optimization.
"""

# ────────────────────────────────────────────────────────────────────────────
# Helper Decorators & Context Managers
# ────────────────────────────────────────────────────────────────────────────

F = TypeVar("F", bound=Callable[..., Any])


def track_latency(
    histogram: Histogram,
    label_values: dict[str, str] | None = None,
) -> Callable[[F], F]:
    """Decorator to track function execution latency.

    Args:
        histogram: Prometheus Histogram object to record latency.
        label_values: Optional dict of label names → values. If provided,
            labels are recorded with the histogram metric.

    Example:
        >>> @track_latency(ontology_validation_latency_ms, {"object_type": "Project"})
        >>> def validate_project(project: Project) -> bool:
        ...     return True

    Returns:
        Decorated function that records latency.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if label_values:
                    histogram.labels(**label_values).observe(elapsed_ms)
                else:
                    histogram.observe(elapsed_ms)

        return wrapper  # type: ignore[return-value]

    return decorator


def track_counter(
    counter: Counter,
    label_values: dict[str, str] | None = None,
) -> Callable[[F], F]:
    """Decorator to increment a counter on function completion.

    Args:
        counter: Prometheus Counter object.
        label_values: Optional dict of label names → values.

    Returns:
        Decorated function that increments counter.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if label_values:
                counter.labels(**label_values).inc()
            else:
                counter.inc()
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


class MetricsContext:
    """Context manager for tracking operation metrics with labels.

    Example:
        >>> with MetricsContext(
        ...     histogram=ontology_validation_latency_ms,
        ...     labels={"object_type": "Project"}
        ... ) as ctx:
        ...     project = Project.model_validate(json_data)
        ...     # Latency automatically recorded on exit
    """

    def __init__(
        self,
        histogram: Histogram | None = None,
        counter: Counter | None = None,
        labels: dict[str, str] | None = None,
    ) -> None:
        self.histogram = histogram
        self.counter = counter
        self.labels = labels or {}
        self.start_time: float | None = None

    def __enter__(self) -> MetricsContext:
        """Record the start time when entering context."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        """Record latency and increment counter if no exception occurred."""
        if self.start_time is not None:
            elapsed_ms = (time.perf_counter() - self.start_time) * 1000
            if self.histogram:
                if self.labels:
                    self.histogram.labels(**self.labels).observe(elapsed_ms)
                else:
                    self.histogram.observe(elapsed_ms)
            if self.counter and exc_type is None:
                if self.labels:
                    self.counter.labels(**self.labels).inc()
                else:
                    self.counter.inc()
        return False  # Propagate exceptions


# ────────────────────────────────────────────────────────────────────────────
# Metrics Export & Bootstrap
# ────────────────────────────────────────────────────────────────────────────


def get_metrics_content() -> bytes:
    """Generate Prometheus text format metrics snapshot.

    Returns:
        UTF-8 encoded Prometheus metrics in text exposition format.

    Usage:
        This is typically called by a metrics endpoint:
        >>> from ontology.metrics import get_metrics_content, CONTENT_TYPE_LATEST
        >>> # In your HTTP framework (FastAPI, Flask, etc.)
        >>> @app.get("/metrics")
        >>> def metrics():
        ...     return Response(get_metrics_content(), media_type=CONTENT_TYPE_LATEST)
    """
    return generate_latest()


def bootstrap_metrics_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Bootstrap a simple metrics HTTP server (for development/testing).

    This function starts a basic HTTP server on the specified host:port
    that exposes metrics at `/metrics` endpoint in Prometheus text format.

    Args:
        host: Bind address (default: "0.0.0.0" for all interfaces).
        port: HTTP port (default: 8000).

    Raises:
        OSError: If port is already in use.

    Example:
        >>> from ontology.metrics import bootstrap_metrics_server
        >>> # In main:
        >>> bootstrap_metrics_server(host="localhost", port=8000)
        >>> # Metrics available at http://localhost:8000/metrics
    """
    try:
        from prometheus_client import start_http_server

        start_http_server(port, addr=host)
        logger.info(
            f"Metrics server bootstrapped on http://{host}:{port}/metrics",
        )
    except ImportError:
        logger.error(
            "prometheus_client not found. "
            "Install with: pip install prometheus-client",
        )
        raise


# ────────────────────────────────────────────────────────────────────────────
# Convenience Functions for Common Instrumentation Patterns
# ────────────────────────────────────────────────────────────────────────────


def record_validation_latency(object_type: str, latency_ms: float) -> None:
    """Record validation latency for a specific object type.

    Args:
        object_type: Name of the object being validated.
        latency_ms: Latency in milliseconds.
    """
    ontology_validation_latency_ms.labels(object_type=object_type).observe(latency_ms)


def record_rule_execution(
    rule_id: str,
    object_type: str,
    latency_ms: float,
) -> None:
    """Record rule execution latency.

    Args:
        rule_id: Unique identifier of the rule.
        object_type: Name of the object being validated.
        latency_ms: Latency in milliseconds.
    """
    ontology_rule_execution_ms.labels(
        rule_id=rule_id,
        object_type=object_type,
    ).observe(latency_ms)


def record_action_execution(
    action_type: str,
    autonomy_level: str,
    latency_ms: float,
    status: str = "success",
) -> None:
    """Record action execution with latency and status.

    Args:
        action_type: Action class name.
        autonomy_level: One of: autonomous, human_approved, human_directed.
        latency_ms: Execution latency in milliseconds.
        status: Execution status (success, validation_error, rule_violation, unknown_error).
    """
    action_execution_time_ms.labels(
        action_type=action_type,
        autonomy_level=autonomy_level,
    ).observe(latency_ms)

    action_execution_total.labels(
        action_type=action_type,
        status=status,
    ).inc()


def record_worklog_parse(status: str) -> None:
    """Record WorkLog parsing attempt.

    Args:
        status: One of: success, failure, malformed_json.
    """
    worklog_parse_total.labels(status=status).inc()


def record_decision_creation(decision_type: str) -> None:
    """Record Decision object creation (KPI metric).

    Args:
        decision_type: Category of decision created.
    """
    decision_created_total.labels(decision_type=decision_type).inc()


def record_compliance_violation(validator_type: str) -> None:
    """Increment compliance violation counter.

    Args:
        validator_type: Type of validator that detected violation.
    """
    compliance_violation_count.labels(validator_type=validator_type).inc()


def update_cache_hit_ratio(ratio: float) -> None:
    """Update cache hit ratio gauge.

    Args:
        ratio: Hit ratio as float in [0.0, 1.0].

    Raises:
        ValueError: If ratio not in valid range.
    """
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"Cache hit ratio must be in [0.0, 1.0], got {ratio}")
    ontology_cache_hit_ratio.set(ratio)


def update_object_count(object_type: str, count: int) -> None:
    """Update object count gauge for a specific type.

    Args:
        object_type: Name of the object type.
        count: Total count of objects in system.
    """
    ontology_object_count.labels(object_type=object_type).set(count)


def update_error_rate(rate: float) -> None:
    """Update current error rate gauge.

    Args:
        rate: Error rate as float in [0.0, 1.0] (typically 5-min rolling window).

    Raises:
        ValueError: If rate not in valid range.
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"Error rate must be in [0.0, 1.0], got {rate}")
    ontology_error_rate.set(rate)


def update_connection_pool_usage(usage: float) -> None:
    """Update database connection pool usage gauge.

    Args:
        usage: Pool utilization as float in [0.0, 1.0].

    Raises:
        ValueError: If usage not in valid range.
    """
    if not 0.0 <= usage <= 1.0:
        raise ValueError(f"Pool usage must be in [0.0, 1.0], got {usage}")
    db_connection_pool_usage.set(usage)
