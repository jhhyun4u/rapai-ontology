"""Rule Registry: SSOT for all 16 core business rules (R001-R016).

Each rule is defined with:
  - rule_id: Unique identifier (e.g., 'R001')
  - sbvr_statement: Human-readable SBVR specification
  - severity: Deontic modality (MUST, SHOULD, MAY)
  - affected_entities: Entity types rule applies to
  - condition: Evaluation function (lambda or callable)
"""

from __future__ import annotations

from typing import Any

from ontology.rules.engine import Rule, RuleSeverity


class RuleRegistry:
    """Global registry of all business rules.

    Rules are organized by ID (R001-R013) and can be queried by ID or entity type.
    """

    def __init__(self) -> None:
        """Initialize with 16 core rules (R001-R016)."""
        self._rules: dict[str, Rule] = {}
        self._build_rules()

    def _build_rules(self) -> None:
        """Build all 13 core rules."""

        # ──── R001: Blocker Resolution → Task Progress (24h) ────
        def r001_condition(context: dict[str, Any]) -> bool:
            """If Blocker(severity='critical') is resolved,
            Task must transition from 'blocked' within 24h.
            """
            blocker_status = context.get('status')
            blocker_severity = context.get('severity')

            # Only applies to critical blockers
            if blocker_severity != 'critical' or blocker_status != 'resolved':
                return True  # Not applicable

            task_status = context.get('task_status')
            if task_status != 'blocked':
                return True  # Task not in blocked state (satisfied)

            # Check 24h window
            elapsed_hours = context.get('elapsed_hours')
            if elapsed_hours is not None:
                return bool(elapsed_hours < 24)

            # If resolved_at and current status timestamp given, calculate
            resolved_at_str = context.get('resolved_at')
            task_status_at_str = context.get('task_status_at')
            if resolved_at_str and task_status_at_str:
                try:
                    from datetime import datetime
                    resolved = datetime.fromisoformat(resolved_at_str.replace('Z', '+00:00'))
                    status_at = datetime.fromisoformat(task_status_at_str.replace('Z', '+00:00'))
                    diff = (status_at - resolved).total_seconds() / 3600
                    return diff < 24
                except:
                    pass

            return True  # Can't determine without full timestamp data

        self._rules['R001'] = Rule(
            rule_id='R001',
            sbvr_statement=(
                'If a Blocker with severity="critical" is resolved, '
                'the parent Task must transition from "blocked" to "planned" or "in_progress" within 24 hours.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Blocker', 'Task'],
            condition=r001_condition
        )

        # ──── R002: TRL/CRL Gate Prerequisite ────
        def r002_condition(context: dict[str, Any]) -> bool:
            """Project type A or B must have Gate(level='L1_TRL', status='passed')
            before Task can transition to 'done'.
            """
            project_type = context.get('project_type')

            # Type string might be ProjectTypeCode enum or string
            if isinstance(project_type, str):
                project_type = project_type.upper()

            if project_type not in ('A', 'B'):
                return True  # No requirement for types C-H

            gates = context.get('gates', [])
            if not gates:
                return False  # No gates found

            # Check for TRL gate (level='L1_TRL' and status='passed')
            for gate in gates:
                if gate.get('level') == 'L1_TRL' or (hasattr(gate, 'level') and gate.level == 'L1_TRL'):
                    if gate.get('status') == 'passed' or (hasattr(gate, 'status') and gate.status == 'passed'):
                        return True  # Found passed TRL gate

            return False  # No passed TRL gate found

        self._rules['R002'] = Rule(
            rule_id='R002',
            sbvr_statement=(
                'Project type "A" or "B" must have Gate(level="L1_TRL", status="passed") '
                'before any Task.status → "done".'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Project', 'Task', 'Gate'],
            condition=r002_condition
        )

        # ──── R003: Contract Research → L2-C Gate ────
        def r003_condition(context: dict[str, Any]) -> bool:
            """If Project.contract_modality='contract_research',
            exactly one Gate(level='L2_C_CLIENT') must exist.
            """
            modality = context.get('contract_modality')
            if modality != 'contract_research':
                return True  # No requirement

            gates = context.get('gates', [])
            l2c_gates = [g for g in gates if g.get('level') == 'L2_C_CLIENT']
            return len(l2c_gates) >= 1

        self._rules['R003'] = Rule(
            rule_id='R003',
            sbvr_statement=(
                'If Project.contract_modality="contract_research", '
                'exactly one Gate(level="L2_C_CLIENT") must exist and be scheduled.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Project', 'Gate'],
            condition=r003_condition
        )

        # ──── R004: Task Dependency Acyclicity ────
        def r004_condition(context: dict[str, Any]) -> bool:
            """No Task may indirectly depend on itself (no cycles in depends_on).
            Simplified: check if dependencies form a DAG.
            """
            dependencies = context.get('dependencies', {})
            if not dependencies:
                return True  # No dependencies = acyclic

            # Simple cycle detection: check for self-loops and 2-node cycles
            for task_id, deps in dependencies.items():
                if task_id in deps:
                    return False  # Self-reference (cycle)

                # Check 2-node cycle: A → B → A
                for dep in deps:
                    if task_id in dependencies.get(dep, []):
                        return False  # Cycle detected

            return True  # Acyclic

        self._rules['R004'] = Rule(
            rule_id='R004',
            sbvr_statement=(
                'No Task may indirectly depend on itself '
                '(no cycles in Task→Task depends_on relationship).'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Task'],
            condition=r004_condition
        )

        # ──── R005: Decision Option Completeness ────
        def r005_condition(context: dict[str, Any]) -> bool:
            """Every Decision must have ≥2 options,
            each with unique option_id, chosen must reference one.
            """
            options = context.get('options', [])
            if len(options) < 2:
                return False  # Need ≥2 options

            option_ids = [opt.get('option_id') for opt in options]
            if len(option_ids) != len(set(option_ids)):
                return False  # Duplicate option_ids

            chosen = context.get('chosen')
            return chosen in option_ids

        self._rules['R005'] = Rule(
            rule_id='R005',
            sbvr_statement=(
                'Every Decision must have ≥2 options, '
                'each with unique option_id, and chosen must reference one option_id.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Decision'],
            condition=r005_condition
        )

        # ──── R006: KPI Measurement Periodicity ────
        def r006_condition(context: dict[str, Any]) -> bool:
            """If KPI.frequency='daily', actual measurement must exist within 24h.
            If 'weekly', within 7 days.
            """
            frequency = context.get('frequency')
            if frequency is None:
                return True  # No frequency requirement

            created_at_str = context.get('created_at')
            measured_at_str = context.get('measured_at')

            if not measured_at_str:
                return False  # Not yet measured

            # Simplified: check if measurement_due_date exists
            if frequency == 'daily':
                return True  # Would check: measured_at within 24h
            elif frequency == 'weekly':
                return True  # Would check: measured_at within 7 days

            return True

        self._rules['R006'] = Rule(
            rule_id='R006',
            sbvr_statement=(
                'If KPI.frequency="daily", actual measurement must exist within 24h of creation; '
                'if "weekly", within 7 days.'
            ),
            severity=RuleSeverity.SHOULD,
            affected_entities=['KPI'],
            condition=r006_condition
        )

        # ──── R007: Artifact Hash Integrity ────
        def r007_condition(context: dict[str, Any]) -> bool:
            """If Artifact.hash is set, subsequent versions must update hash if content changed.
            """
            artifact_hash = context.get('hash')
            if not artifact_hash:
                return True  # No hash set = no requirement

            # Would check: previous version hash vs current
            return True  # Simplified: assume valid

        self._rules['R007'] = Rule(
            rule_id='R007',
            sbvr_statement=(
                'If Artifact.hash is set, subsequent versions must either '
                'retain hash (no change) or update hash (content changed).'
            ),
            severity=RuleSeverity.SHOULD,
            affected_entities=['Artifact'],
            condition=r007_condition
        )

        # ──── R008: Risk Mitigation Trigger ────
        def r008_condition(context: dict[str, Any]) -> bool:
            """If Risk(likelihood='likely' or 'almost_certain') AND impact='critical',
            Blocker must be raised within 48h.
            """
            likelihood = context.get('likelihood')
            impact = context.get('impact')

            if likelihood not in ('likely', 'almost_certain') or impact != 'critical':
                return True  # No requirement

            blocker_id = context.get('blocker_id')
            created_at_str = context.get('created_at')

            if not blocker_id:
                return False  # Blocker not raised

            return True  # Blocker exists

        self._rules['R008'] = Rule(
            rule_id='R008',
            sbvr_statement=(
                'If Risk.likelihood="likely" or "almost_certain" '
                'AND Risk.impact="critical", a Blocker must be raised within 48h.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Risk', 'Blocker'],
            condition=r008_condition
        )

        # ──── R009: IP Filing Progression ────
        def r009_condition(context: dict[str, Any]) -> bool:
            """IP.status transitions follow order:
            idea → drafting → filed → published → [granted|rejected|abandoned]
            """
            status = context.get('status')
            valid_order = ['idea', 'drafting', 'filed', 'published', 'granted', 'rejected', 'abandoned']

            if status not in valid_order:
                return False

            # Would check: previous status is earlier in order
            return True  # Simplified

        self._rules['R009'] = Rule(
            rule_id='R009',
            sbvr_statement=(
                'IP.status transitions follow order: '
                'idea → drafting → filed → published → [granted|rejected|abandoned].'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['IP'],
            condition=r009_condition
        )

        # ──── R010: WorkDirective Intent → Action Mapping ────
        def r010_condition(context: dict[str, Any]) -> bool:
            """Every WorkDirective.intent must map to ≥1 executable Action
            with valid Intent enum value.
            """
            intent = context.get('intent')
            valid_intents = {
                'create_task', 'update_status', 'log_work', 'assign_person',
                'raise_blocker', 'resolve_blocker', 'record_decision',
                'submit_gate', 'measure_kpi', 'produce_artifact'
            }

            return intent in valid_intents

        self._rules['R010'] = Rule(
            rule_id='R010',
            sbvr_statement=(
                'Every WorkDirective.intent must map to ≥1 executable Action '
                'with valid Intent enum value.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['WorkDirective'],
            condition=r010_condition
        )

        # ──── R011: Append-Only GATE ────
        def r011_condition(context: dict[str, Any]) -> bool:
            """Gate records cannot be deleted, only status='waived'."""
            action = context.get('action')
            if action != 'delete':
                return True  # Not a delete action

            return False  # Deletes not allowed

        self._rules['R011'] = Rule(
            rule_id='R011',
            sbvr_statement='Gate records cannot be deleted, only status="waived".',
            severity=RuleSeverity.MUST,
            affected_entities=['Gate'],
            condition=r011_condition
        )

        # ──── R012: Security Tier Monotonicity ────
        def r012_condition(context: dict[str, Any]) -> bool:
            """Task security_tier ≥ parent Project security_tier (dominance)."""
            task_tier = context.get('task_security_tier')
            project_tier = context.get('project_security_tier')

            if not task_tier or not project_tier:
                return True  # Can't determine

            tier_rank = {'PUBLIC': 0, 'RESTRICTED': 1, 'CONFIDENTIAL': 2, 'SECRET': 3}
            task_rank = tier_rank.get(task_tier, -1)
            proj_rank = tier_rank.get(project_tier, -1)

            return task_rank >= proj_rank

        self._rules['R012'] = Rule(
            rule_id='R012',
            sbvr_statement=(
                'Task security_tier ≥ parent Project security_tier '
                '(no downgrade of sensitivity).'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Task', 'Project'],
            condition=r012_condition
        )

        # ──── R013: Cross-Cutting Consistency ────
        def r013_condition(context: dict[str, Any]) -> bool:
            """All Project Tasks must share contract_modality."""
            project_modality = context.get('project_contract_modality')
            task_modalities = context.get('task_contract_modalities', [])

            if not task_modalities:
                return True  # No tasks = satisfied

            return all(mod == project_modality for mod in task_modalities)

        self._rules['R013'] = Rule(
            rule_id='R013',
            sbvr_statement=(
                'All Project Tasks must share contract_modality '
                '(inherited from Project level).'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Project', 'Task'],
            condition=r013_condition
        )

        # ──── R014: TRL Level-Up Definition of Done Validation ────
        def r014_condition(context: dict[str, Any]) -> bool:
            """Every TRL level-up (Project.current_trl += 1) must be preceded by
            submission of all required deliverables in DefinitionOfDone and
            approval by Gate(L1_TRL, status='approved').
            """
            event_type: str | None = context.get('event_type')
            if event_type != 'TRL_LEVEL_UP':
                return True  # Not a level-up event

            # Check all required deliverables submitted
            required_artifacts: list[Any] = context.get('required_artifacts', [])
            submitted_artifacts: list[Any] = context.get('submitted_artifacts', [])

            if not all(artifact in submitted_artifacts for artifact in required_artifacts):
                return False  # Missing deliverables

            # Check Gate approval
            gate_approved: bool = context.get('gate_approved', False)
            return bool(gate_approved)

        self._rules['R014'] = Rule(
            rule_id='R014',
            sbvr_statement=(
                'Every TRL level-up must be preceded by submission of all required deliverables '
                'in DefinitionOfDone and approval by Gate(L1_TRL).'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Project', 'Gate', 'Artifact'],
            condition=r014_condition
        )

        # ──── R015: TRL Level-Up Decision Traceability ────
        def r015_condition(context: dict[str, Any]) -> bool:
            """Every TRL level-up must have a DecisionTrace linking:
            - WorkLog entries that provided evidence
            - Gate approval decision
            - Agent auto-decision
            - PROV-O lineage with explainability_score ≥ 0.8
            """
            event_type: str | None = context.get('event_type')
            if event_type != 'TRL_LEVEL_UP':
                return True  # Not a level-up event

            has_decision_trace: bool = context.get('has_decision_trace', False)
            if not has_decision_trace:
                return False

            explainability_score: float = context.get('explainability_score', 0.0)
            return bool(explainability_score >= 0.8)

        self._rules['R015'] = Rule(
            rule_id='R015',
            sbvr_statement=(
                'Every TRL level-up must have a DecisionTrace with PROV-O lineage '
                '(explainability_score ≥ 0.8).'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Project', 'DecisionTrace'],
            condition=r015_condition
        )

        # ──── R016: Backward-Chaining Task Generation for TRL Gap ────
        def r016_condition(context: dict[str, Any]) -> bool:
            """If Project.current_trl < Project.trl_target,
            the system MUST auto-generate intermediate Tasks for each TRL level gap,
            with estimated_hours derived from HistoricalProgressData or
            DefinitionOfDone recommendations.
            """
            current_trl: int | None = context.get('current_trl')
            trl_target: int | None = context.get('trl_target')

            if not current_trl or not trl_target:
                return True  # Can't determine

            if current_trl >= trl_target:
                return True  # No gap = satisfied

            # Check if intermediate tasks were auto-generated
            auto_generated_tasks: list[Any] = context.get('auto_generated_tasks', [])
            expected_task_count = trl_target - current_trl

            return len(auto_generated_tasks) >= expected_task_count

        self._rules['R016'] = Rule(
            rule_id='R016',
            sbvr_statement=(
                'If Project.current_trl < Project.trl_target, '
                'the system MUST auto-generate intermediate Tasks for each TRL level gap.'
            ),
            severity=RuleSeverity.SHOULD,
            affected_entities=['Project', 'Task'],
            condition=r016_condition
        )

        # ── R017: Constraints as Properties (P0 enhancement) ──────────────────
        def r017_condition(context: dict[str, Any]) -> bool:
            """Project budget and headcount constraints must be enforced."""
            max_budget = context.get('max_budget')
            approved_headcount = context.get('approved_headcount_limit')
            security_clearance = context.get('mandatory_security_clearance')
            current_budget = context.get('current_budget', 0.0)
            current_headcount = context.get('current_headcount', 0)

            # If constraints are set, enforce them
            if max_budget is not None and current_budget > max_budget:
                return False
            if approved_headcount is not None and current_headcount > approved_headcount:
                return False

            return True

        self._rules['R017'] = Rule(
            rule_id='R017',
            sbvr_statement=(
                'Every Project MUST enforce its max_budget, approved_headcount_limit, '
                'and mandatory_security_clearance constraints during task allocation.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['Project', 'Task', 'Person'],
            condition=r017_condition
        )

        # ── R020: Provenance Links (P0 enhancement) ───────────────────────────
        def r020_condition(context: dict[str, Any]) -> bool:
            """WorkDirective must have provenance tracking (source_worklog_id or source_rule_ids)."""
            source_worklog_id = context.get('source_worklog_id')
            source_rule_ids = context.get('source_rule_ids')
            source_document = context.get('source_document')

            # At least one provenance source must be specified
            has_provenance = (
                source_worklog_id is not None or
                (source_rule_ids and len(source_rule_ids) > 0) or
                source_document is not None
            )

            return has_provenance

        self._rules['R020'] = Rule(
            rule_id='R020',
            sbvr_statement=(
                'Every WorkDirective MUST have at least one provenance source: '
                'source_worklog_id, source_rule_ids, or source_document.'
            ),
            severity=RuleSeverity.MUST,
            affected_entities=['WorkDirective'],
            condition=r020_condition
        )

    def get(self, rule_id: str) -> Rule:
        """Get rule by ID.

        Args:
            rule_id: Rule ID (e.g., 'R001')

        Returns:
            Rule object

        Raises:
            KeyError: If rule not found
        """
        if rule_id not in self._rules:
            raise KeyError(f"Rule {rule_id} not found in registry")
        return self._rules[rule_id]

    def list_all(self) -> list[Rule]:
        """Return all rules."""
        return list(self._rules.values())

    def list_by_entity(self, entity_type: str) -> list[Rule]:
        """Return rules that apply to a specific entity type."""
        return [r for r in self._rules.values() if entity_type in r.affected_entities]

    def list_by_severity(self, severity: RuleSeverity) -> list[Rule]:
        """Return rules with specific severity."""
        return [r for r in self._rules.values() if r.severity == severity]
