"""Example: Integrating Prometheus metrics with RAPai Ontology.

This module demonstrates how to instrument validation, rule execution,
and action execution with Prometheus metrics for operational monitoring.

Phase II, Week 11 — Metrics Infrastructure Foundation.
"""

from __future__ import annotations

import time
from typing import Any

from ontology.metrics import (
    MetricsContext,
    action_execution_time_ms,
    ontology_rule_execution_ms,
    ontology_validation_latency_ms,
    record_action_execution,
    record_validation_latency,
    track_latency,
    update_cache_hit_ratio,
)

# ────────────────────────────────────────────────────────────────────────────
# Example 1: Tracking validation latency with decorator
# ────────────────────────────────────────────────────────────────────────────


@track_latency(
    ontology_validation_latency_ms,
    label_values={"object_type": "Project"},
)
def validate_project_with_decorator(project_dict: dict[str, Any]) -> bool:
    """Example: Validate a Project with automatic latency tracking.

    The @track_latency decorator records execution time to the
    ontology_validation_latency_ms histogram with object_type="Project".

    This integrates seamlessly with Pydantic validation:
        @track_latency(...)
        def validate_project(project_dict):
            return Project.model_validate(project_dict)
    """
    # Simulate validation
    time.sleep(0.0005)
    return "project_id" in project_dict and "name" in project_dict


# ────────────────────────────────────────────────────────────────────────────
# Example 2: Manual latency tracking with context manager
# ────────────────────────────────────────────────────────────────────────────


def validate_task_with_context(task_dict: dict[str, Any]) -> bool:
    """Example: Validate a Task with manual context manager.

    The MetricsContext context manager records latency on exit.
    This is useful when you cannot use decorators (e.g., in __init__ methods).
    """
    with MetricsContext(
        histogram=ontology_validation_latency_ms,
        labels={"object_type": "Task"},
    ):
        # Simulate validation
        time.sleep(0.0003)
        return "task_id" in task_dict and "title" in task_dict


# ────────────────────────────────────────────────────────────────────────────
# Example 3: Rule execution instrumentation
# ────────────────────────────────────────────────────────────────────────────


def evaluate_rule_with_metrics(
    rule_id: str,
    object_type: str,
    obj: dict[str, Any],
) -> bool:
    """Example: Evaluate a constraint rule and record latency.

    This pattern integrates with the rule engine to track each rule's
    execution time, helping identify slow validators.

    Business use case: If ontology_rule_execution_ms P99 > 0.1ms,
    investigate the offending rule for optimization opportunities.
    """
    start = time.perf_counter()

    try:
        # Simulate rule evaluation logic
        time.sleep(0.00003)  # ~30 microseconds
        passed = obj.get("status") in ("active", "draft")
        return passed
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        from ontology.metrics import record_rule_execution

        record_rule_execution(
            rule_id=rule_id,
            object_type=object_type,
            latency_ms=elapsed_ms,
        )


# ────────────────────────────────────────────────────────────────────────────
# Example 4: Action execution with full context
# ────────────────────────────────────────────────────────────────────────────


def execute_create_task_action(
    task_data: dict[str, Any],
    autonomy_level: str,
) -> dict[str, Any]:
    """Example: Execute a CreateTask action with comprehensive metrics.

    This demonstrates the full instrumentation pattern:
    - Latency tracking (action_execution_time_ms)
    - Status classification (success/validation_error/rule_violation)
    - Counter increment for throughput monitoring

    Business meaning: Tracks domain operation performance and error rate
    by action type and autonomy level (autonomous vs human_approved).
    """
    start = time.perf_counter()
    status = "success"

    try:
        # Simulate action execution with validation
        time.sleep(0.008)

        # Validation check
        if not task_data.get("title"):
            status = "validation_error"
            return {"error": "title required"}

        # Rule evaluation
        if task_data.get("wbs_code") and not _validate_wbs(
            task_data["wbs_code"],
        ):
            status = "rule_violation"
            return {"error": "invalid WBS code"}

        # Success path
        return {"task_id": "TSK-12345", "status": "created"}

    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        record_action_execution(
            action_type="CreateTask",
            autonomy_level=autonomy_level,
            latency_ms=elapsed_ms,
            status=status,
        )


def _validate_wbs(wbs_code: str) -> bool:
    """Helper: Validate WBS code format (e.g., '1.2.3')."""
    import re

    return bool(re.match(r"^\d+(\.\d+)*$", wbs_code))


# ────────────────────────────────────────────────────────────────────────────
# Example 5: Cache hit ratio monitoring
# ────────────────────────────────────────────────────────────────────────────


def update_cache_metrics(
    total_requests: int,
    cache_hits: int,
) -> None:
    """Example: Update cache hit ratio gauge.

    SLO target: > 0.70 (70% hit ratio)

    Business meaning: Higher hit ratio reduces downstream latency.
    If ratio drops below 0.70, investigate:
    - Cache invalidation frequency
    - Working set size vs. cache capacity
    - Cache key design (too granular?)
    """
    if total_requests > 0:
        ratio = cache_hits / total_requests
        update_cache_hit_ratio(ratio)
        print(f"Cache hit ratio: {ratio:.2%} ({cache_hits}/{total_requests})")

        if ratio < 0.70:
            print("WARNING: Cache hit ratio below SLO (70%)")


# ────────────────────────────────────────────────────────────────────────────
# Example 6: Compliance violation tracking
# ────────────────────────────────────────────────────────────────────────────


def record_validation_error(
    violation_type: str,
    object_id: str,
) -> None:
    """Example: Record compliance violations.

    Tracks constraint violations by type:
    - trl_gate: TRL progression rule violated
    - crl_gate: CRL progression rule violated
    - wbs_validity: WBS code format invalid
    - etc.

    Business meaning: Should trend toward 0. Spike indicates rule design
    issue or data corruption.
    """
    from ontology.metrics import record_compliance_violation

    record_compliance_violation(validator_type=violation_type)
    print(
        f"Compliance violation recorded: {violation_type} "
        f"(object: {object_id})",
    )


# ────────────────────────────────────────────────────────────────────────────
# Example 7: Full integration pattern
# ────────────────────────────────────────────────────────────────────────────


def full_action_workflow(
    action_type: str,
    action_data: dict[str, Any],
) -> tuple[bool, str]:
    """Full workflow showing validation → rules → action execution.

    This example demonstrates how metrics flow through the entire
    ontology operation pipeline.
    """
    from ontology.metrics import record_compliance_violation as record_violation

    # Step 1: Validate input
    with MetricsContext(
        histogram=ontology_validation_latency_ms,
        labels={"object_type": action_type},
    ):
        is_valid = "data" in action_data
        if not is_valid:
            record_validation_latency(action_type, 0.001)
            return False, "validation_error"

    # Step 2: Evaluate rules
    rules = [
        ("RULE-001-REQUIRED-FIELDS", action_type),
        ("RULE-002-CROSS-REFERENCE", action_type),
    ]

    for rule_id, obj_type in rules:
        if not evaluate_rule_with_metrics(rule_id, obj_type, action_data):
            record_violation(validator_type=rule_id)
            return False, "rule_violation"

    # Step 3: Execute action
    if action_type == "CreateTask":
        result = execute_create_task_action(action_data, "autonomous")
        return "error" not in result, "success"

    return True, "success"


# ────────────────────────────────────────────────────────────────────────────
# Main: Demo execution
# ────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("=" * 70)
    print("RAPai Ontology Metrics Integration Examples")
    print("=" * 70)
    print()

    # Example 1: Decorator-based latency tracking
    print("Example 1: Validation with decorator")
    print("-" * 70)
    result = validate_project_with_decorator({"project_id": "P123", "name": "Test"})
    print(f"Validation result: {result}")
    print()

    # Example 2: Context manager tracking
    print("Example 2: Validation with context manager")
    print("-" * 70)
    result = validate_task_with_context({"task_id": "T456", "title": "Review"})
    print(f"Validation result: {result}")
    print()

    # Example 3: Rule evaluation
    print("Example 3: Rule evaluation with latency")
    print("-" * 70)
    result = evaluate_rule_with_metrics(
        "RULE-001-STATUS-CHECK",
        "Task",
        {"status": "active"},
    )
    print(f"Rule passed: {result}")
    print()

    # Example 4: Action execution
    print("Example 4: Action execution (CreateTask)")
    print("-" * 70)
    result = execute_create_task_action(
        {
            "title": "Implement feature",
            "wbs_code": "1.2.3",
        },
        "autonomous",
    )
    print(f"Action result: {result}")
    print()

    # Example 5: Cache metrics
    print("Example 5: Cache hit ratio monitoring")
    print("-" * 70)
    update_cache_metrics(total_requests=100, cache_hits=78)
    print()

    # Example 6: Compliance violations
    print("Example 6: Compliance violation tracking")
    print("-" * 70)
    record_validation_error("trl_gate", "P-001")
    print()

    # Example 7: Full workflow
    print("Example 7: Full workflow integration")
    print("-" * 70)
    success, status = full_action_workflow(
        "CreateTask",
        {"data": {"title": "Test", "wbs_code": "1.0"}},
    )
    print(f"Workflow success: {success}, status: {status}")
    print()

    # Export metrics
    print("Exporting Prometheus metrics...")
    print("-" * 70)
    from ontology.metrics import get_metrics_content

    metrics = get_metrics_content()
    print(f"Total metrics size: {len(metrics)} bytes")
    print("Sample output:")
    lines = metrics.decode().split("\n")
    # Print non-Python-internal metrics
    custom_metrics = [
        line for line in lines if "ontology_" in line or "action_" in line
    ]
    for line in custom_metrics[:10]:
        print(f"  {line}")

    print()
    print("=" * 70)
    print("Examples complete! Access metrics at http://localhost:8000/metrics")
    print("                  after calling: bootstrap_metrics_server()")
    print("=" * 70)
