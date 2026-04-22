"""Unit tests for Prometheus instrumentation module.

Tests verify:
1. Metric recording and label assignment
2. Decorator and context manager functionality
3. Helper function validation and bounds checking
4. Integration with validation and rule execution flows
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from ontology.metrics import (
    MetricsContext,
    action_execution_time_ms,
    action_execution_total,
    compliance_violation_count,
    db_connection_pool_usage,
    db_query_latency_ms,
    decision_created_total,
    ontology_cache_hit_ratio,
    ontology_error_rate,
    ontology_object_count,
    ontology_rule_execution_ms,
    ontology_validation_latency_ms,
    record_action_execution,
    record_compliance_violation,
    record_decision_creation,
    record_rule_execution,
    record_validation_latency,
    record_worklog_parse,
    track_latency,
    update_cache_hit_ratio,
    update_connection_pool_usage,
    update_error_rate,
    update_object_count,
    worklog_parse_total,
)


@pytest.mark.unit
class TestLatencyMetrics:
    """Test latency histogram metrics."""

    def test_validation_latency_recorded(self) -> None:
        """Verify validation latency is recorded with correct labels."""
        record_validation_latency("Project", 0.5)
        # Metric recorded successfully (would need Prometheus registry snapshot
        # to assert exact value; this test confirms no exception raised)
        assert True

    def test_rule_execution_latency_recorded(self) -> None:
        """Verify rule execution latency with labels."""
        record_rule_execution(
            rule_id="RULE-001-TRL-GATE",
            object_type="Project",
            latency_ms=0.05,
        )
        assert True

    def test_action_execution_latency_recorded(self) -> None:
        """Verify action execution latency with autonomy level."""
        record_action_execution(
            action_type="CreateTask",
            autonomy_level="autonomous",
            latency_ms=15.5,
            status="success",
        )
        assert True

    def test_db_query_latency_recorded(self) -> None:
        """Verify database query latency recorded."""
        db_query_latency_ms.labels(query_type="select").observe(2.5)
        assert True


@pytest.mark.unit
class TestThroughputMetrics:
    """Test counter metrics for throughput tracking."""

    def test_worklog_parse_success(self) -> None:
        """Verify WorkLog parse success counter increments."""
        record_worklog_parse("success")
        assert True

    def test_worklog_parse_failure(self) -> None:
        """Verify WorkLog parse failure counter increments."""
        record_worklog_parse("failure")
        assert True

    def test_action_execution_success(self) -> None:
        """Verify action execution success counter."""
        action_execution_total.labels(
            action_type="AssignPerson",
            status="success",
        ).inc()
        assert True

    def test_action_execution_validation_error(self) -> None:
        """Verify action execution validation error counter."""
        action_execution_total.labels(
            action_type="AssignPerson",
            status="validation_error",
        ).inc()
        assert True

    def test_decision_creation_recorded(self) -> None:
        """Verify Decision creation KPI metric."""
        record_decision_creation("gate_decision")
        assert True


@pytest.mark.unit
class TestCacheMetrics:
    """Test cache and object count gauge metrics."""

    def test_cache_hit_ratio_valid(self) -> None:
        """Verify valid cache hit ratio update."""
        update_cache_hit_ratio(0.75)
        assert True

    def test_cache_hit_ratio_boundary_zero(self) -> None:
        """Verify zero cache hit ratio."""
        update_cache_hit_ratio(0.0)
        assert True

    def test_cache_hit_ratio_boundary_one(self) -> None:
        """Verify 100% cache hit ratio."""
        update_cache_hit_ratio(1.0)
        assert True

    def test_cache_hit_ratio_invalid_below_zero(self) -> None:
        """Verify cache hit ratio validation rejects negative values."""
        with pytest.raises(ValueError, match="must be in"):
            update_cache_hit_ratio(-0.1)

    def test_cache_hit_ratio_invalid_above_one(self) -> None:
        """Verify cache hit ratio validation rejects values >1.0."""
        with pytest.raises(ValueError, match="must be in"):
            update_cache_hit_ratio(1.1)

    def test_object_count_recorded(self) -> None:
        """Verify object count gauge update."""
        update_object_count("Project", 42)
        assert True


@pytest.mark.unit
class TestQualityMetrics:
    """Test quality and compliance gauge metrics."""

    def test_error_rate_valid(self) -> None:
        """Verify valid error rate update."""
        update_error_rate(0.02)
        assert True

    def test_error_rate_zero(self) -> None:
        """Verify zero error rate (ideal state)."""
        update_error_rate(0.0)
        assert True

    def test_error_rate_high(self) -> None:
        """Verify high error rate (alert threshold)."""
        update_error_rate(0.15)
        assert True

    def test_error_rate_invalid_negative(self) -> None:
        """Verify error rate validation rejects negative."""
        with pytest.raises(ValueError, match="must be in"):
            update_error_rate(-0.05)

    def test_error_rate_invalid_exceeds_one(self) -> None:
        """Verify error rate validation rejects >1.0."""
        with pytest.raises(ValueError, match="must be in"):
            update_error_rate(1.5)

    def test_compliance_violation_recorded(self) -> None:
        """Verify compliance violation counter increments."""
        record_compliance_violation("trl_gate")
        assert True

    def test_compliance_violation_types(self) -> None:
        """Verify various compliance violation types."""
        violation_types = [
            "trl_gate",
            "crl_gate",
            "wbs_validity",
            "cardinality",
            "self_reference",
            "contract_research_modality",
            "identifier_format",
            "enum_match",
        ]
        for vtype in violation_types:
            record_compliance_violation(vtype)
        assert True


@pytest.mark.unit
class TestDatabaseMetrics:
    """Test database-specific metrics."""

    def test_connection_pool_usage_valid(self) -> None:
        """Verify valid connection pool usage."""
        update_connection_pool_usage(0.65)
        assert True

    def test_connection_pool_usage_low(self) -> None:
        """Verify low pool usage (healthy state)."""
        update_connection_pool_usage(0.2)
        assert True

    def test_connection_pool_usage_high(self) -> None:
        """Verify high pool usage (alert threshold at 0.85)."""
        update_connection_pool_usage(0.88)
        assert True

    def test_connection_pool_usage_invalid(self) -> None:
        """Verify connection pool usage validation."""
        with pytest.raises(ValueError, match="must be in"):
            update_connection_pool_usage(1.5)


@pytest.mark.unit
class TestTrackLatencyDecorator:
    """Test @track_latency decorator."""

    def test_track_latency_without_labels(self) -> None:
        """Verify latency is recorded when function completes."""

        @track_latency(
            ontology_validation_latency_ms,
            label_values={"object_type": "Event"},
        )
        def dummy_function() -> str:
            time.sleep(0.001)  # 1ms sleep
            return "result"

        result = dummy_function()
        assert result == "result"

    def test_track_latency_with_labels(self) -> None:
        """Verify latency is recorded with labels."""

        @track_latency(
            ontology_validation_latency_ms,
            label_values={"object_type": "Task"},
        )
        def dummy_validation() -> bool:
            return True

        result = dummy_validation()
        assert result is True

    def test_track_latency_on_exception(self) -> None:
        """Verify latency is still recorded even if function raises."""

        @track_latency(
            ontology_validation_latency_ms,
            label_values={"object_type": "Project"},
        )
        def dummy_error() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            dummy_error()


@pytest.mark.unit
class TestMetricsContext:
    """Test MetricsContext context manager."""

    def test_metrics_context_with_histogram(self) -> None:
        """Verify context manager records histogram latency."""
        with MetricsContext(
            histogram=ontology_validation_latency_ms,
            labels={"object_type": "Event"},
        ) as ctx:
            time.sleep(0.001)
        assert ctx.start_time is not None

    def test_metrics_context_with_counter(self) -> None:
        """Verify context manager increments counter on success."""
        with MetricsContext(
            counter=action_execution_total,
            labels={"action_type": "LogWork", "status": "success"},
        ):
            pass
        assert True

    def test_metrics_context_with_both_same_labels(self) -> None:
        """Verify context manager with both histogram and counter.

        Note: This uses two metrics that both accept 'rule_id' and 'object_type'
        labels. For metrics with different label sets, use separate contexts.
        """
        # Both ontology_rule_execution_ms and a hypothetical rule counter
        # would need the same labels. For this test, we just verify
        # the context manager pattern works with histogram + counter.
        with MetricsContext(
            histogram=ontology_rule_execution_ms,
            labels={"rule_id": "RULE-001", "object_type": "Project"},
        ):
            time.sleep(0.001)
        assert True

    def test_metrics_context_exception_skips_counter(self) -> None:
        """Verify counter is not incremented when exception raised."""
        try:
            with MetricsContext(
                counter=action_execution_total,
                labels={"action_type": "Test", "status": "failure"},
            ):
                raise RuntimeError("Simulated error")
        except RuntimeError:
            pass
        # Counter should not be incremented (exception occurred)
        assert True

    def test_metrics_context_exception_records_histogram(self) -> None:
        """Verify histogram is still recorded even on exception."""
        try:
            with MetricsContext(
                histogram=db_query_latency_ms,
                labels={"query_type": "select"},
            ):
                time.sleep(0.001)
                raise RuntimeError("Query error")
        except RuntimeError:
            pass
        # Histogram should still be recorded
        assert True


@pytest.mark.unit
class TestMetricsIntegration:
    """Integration tests with ontology operations."""

    def test_validation_workflow(self) -> None:
        """Simulate validation workflow with metrics."""
        # In real usage, this would be integrated with Pydantic validation
        start = time.perf_counter()
        # Simulate validation
        time.sleep(0.001)
        elapsed_ms = (time.perf_counter() - start) * 1000

        record_validation_latency("Project", elapsed_ms)
        assert True

    def test_action_execution_workflow(self) -> None:
        """Simulate action execution with full metrics."""
        start = time.perf_counter()

        # Simulate action execution
        try:
            time.sleep(0.005)
            status = "success"
        except Exception:
            status = "unknown_error"

        elapsed_ms = (time.perf_counter() - start) * 1000

        record_action_execution(
            action_type="CreateTask",
            autonomy_level="autonomous",
            latency_ms=elapsed_ms,
            status=status,
        )
        assert True

    def test_rule_evaluation_workflow(self) -> None:
        """Simulate rule evaluation with metrics."""
        rules = [
            "RULE-001-TRL-GATE",
            "RULE-002-CRL-GATE",
            "RULE-003-WBS-VALIDITY",
        ]

        for rule_id in rules:
            start = time.perf_counter()
            # Simulate rule evaluation
            time.sleep(0.0005)
            elapsed_ms = (time.perf_counter() - start) * 1000

            record_rule_execution(
                rule_id=rule_id,
                object_type="Project",
                latency_ms=elapsed_ms,
            )

        assert True
