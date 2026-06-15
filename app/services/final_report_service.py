import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.state.pipeline_state import PipelineState


class FinalReportService:
    """
    Builds and saves the final AegisML investigation report.

    The report is designed to be both machine-readable and interview/demo-ready:
    it contains alert context, diagnostic plan, evidence, validation results,
    repair history, root cause, alternatives, remediation, and safety notes.
    """

    def __init__(self, output_dir: str = "outputs/reports") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_report(
        self,
        state: PipelineState,
        plan_quality: Dict,
        plan_validation: Dict,
        root_cause_validation: Dict,
    ) -> Dict:
        report_id = f"REPORT-{state.alert_id}"

        root_cause = state.root_cause.model_dump() if state.root_cause else None
        remediation = state.remediation.model_dump() if state.remediation else None

        serialized_plan_validation = self._serialize_validation(plan_validation)
        serialized_evidence = [item.model_dump() for item in state.evidence]

        report = {
            "report_id": report_id,
            "alert_id": state.alert_id,
            "status": getattr(state, "status", "completed"),

            "executive_summary": self._build_executive_summary(
                state=state,
                root_cause=root_cause,
                remediation=remediation,
            ),

            "alert_context": self._build_alert_context(state),

            "execution_metadata": {
                "investigation_mode": state.alert.get("investigation_mode"),
                "planning_mode": getattr(state, "planning_mode", "deterministic"),
                "root_cause_mode": getattr(state, "root_cause_mode", "deterministic"),
                "replans": state.replans,
                "max_replans": state.max_replans,
                "human_approval_required": self._human_approval_required(remediation),
                "automated_remediation_executed": False,
            },

            "diagnostic_plan": {
                "initial_plan": [step.model_dump() for step in state.initial_plan],
                "final_executed_plan": [step.model_dump() for step in state.plan],
                "plan_quality": plan_quality,
                "plan_validation": serialized_plan_validation,
            },

            "evidence_table": self._build_evidence_table(serialized_evidence),

            "validation": {
                "plan_validation_passed": self._validation_passed(
                    serialized_plan_validation
                ),
                "root_cause_validation_passed": self._validation_passed(
                    root_cause_validation
                ),
                "root_cause_validation": root_cause_validation,
                "validation_failures": self._collect_validation_failures(
                    plan_validation=serialized_plan_validation,
                    root_cause_validation=root_cause_validation,
                ),
            },

            "repair_history": {
                "replans": state.replans,
                "repair_events": state.repair_history,
                "warnings": state.warnings,
            },

            "root_cause": root_cause,

            "alternatives_considered": (
                root_cause.get("alternative_causes", [])
                if root_cause
                else []
            ),

            "remediation": remediation,

            "safety_notes": self._build_safety_notes(remediation),

            "errors": state.errors,

            # Backward-compatible raw fields for existing eval/demo code.
            "model_id": state.model_id,
            "goal": state.goal,
            "alert": state.alert,
            "initial_plan": [step.model_dump() for step in state.initial_plan],
            "final_plan": [step.model_dump() for step in state.plan],
            "plan": [step.model_dump() for step in state.plan],
            "plan_quality": plan_quality,
            "plan_validation": serialized_plan_validation,
            "evidence": serialized_evidence,
            "root_cause_validation": root_cause_validation,
            "replans": state.replans,
            "warnings": state.warnings,
        }

        state.final_report = report
        return report

    def _build_markdown_report(self, report: Dict) -> str:
        alert_context = report.get("alert_context", {})
        execution_metadata = report.get("execution_metadata", {})
        diagnostic_plan = report.get("diagnostic_plan", {})
        validation = report.get("validation", {})
        repair_history = report.get("repair_history", {})
        root_cause = report.get("root_cause") or {}
        remediation = report.get("remediation") or {}

        lines = [
            f"# AegisML Incident Report: {report.get('alert_id')}",
            "",
            "## Executive Summary",
            report.get("executive_summary", "No executive summary available."),
            "",
            "## Alert Context",
            f"- Model: {alert_context.get('model_id')}",
            f"- Version: {alert_context.get('model_version')}",
            f"- Environment: {alert_context.get('environment')}",
            f"- Metric: {alert_context.get('metric')}",
            f"- Current Value: {alert_context.get('current_value')}",
            f"- Baseline Value: {alert_context.get('baseline_value')}",
            f"- Severity: {alert_context.get('severity')}",
            f"- Window: {alert_context.get('window_start')} to {alert_context.get('window_end')}",
            f"- Description: {alert_context.get('description')}",
            "",
            "## Execution Metadata",
            f"- Planning Mode: {execution_metadata.get('planning_mode')}",
            f"- Root Cause Mode: {execution_metadata.get('root_cause_mode')}",
            f"- Replans: {execution_metadata.get('replans')}",
            f"- Max Replans: {execution_metadata.get('max_replans')}",
            f"- Human Approval Required: {execution_metadata.get('human_approval_required')}",
            f"- Automated Remediation Executed: {execution_metadata.get('automated_remediation_executed')}",
            "",
            "## Initial Diagnostic Plan",
        ]

        initial_plan = diagnostic_plan.get("initial_plan", [])
        if initial_plan:
            for step in initial_plan:
                lines.append(
                    f"{step.get('step_id')}. `{step.get('action')}` on `{step.get('target')}`"
                )
                lines.append(f"   - Reason: {step.get('reason')}")
        else:
            lines.append("No initial plan recorded.")

        lines.extend([
            "",
            "## Final Executed Plan",
        ])

        final_plan = diagnostic_plan.get("final_executed_plan", [])
        if final_plan:
            for step in final_plan:
                lines.append(
                    f"{step.get('step_id')}. `{step.get('action')}` on `{step.get('target')}`"
                )
                lines.append(f"   - Reason: {step.get('reason')}")
        else:
            lines.append("No final plan recorded.")

        lines.extend([
            "",
            "## Evidence Table",
            "| # | Source | Supports | Summary |",
            "|---|--------|----------|---------|",
        ])

        evidence_table = report.get("evidence_table", [])
        if evidence_table:
            for item in evidence_table:
                lines.append(
                    "| "
                    f"{item.get('evidence_id')} | "
                    f"{item.get('source')} | "
                    f"`{item.get('supports')}` | "
                    f"{self._escape_markdown_table_text(item.get('summary'))} |"
                )
        else:
            lines.append("| - | - | - | No evidence recorded. |")

        lines.extend([
            "",
            "## Validation",
            f"- Plan Validation Passed: {validation.get('plan_validation_passed')}",
            f"- Root Cause Validation Passed: {validation.get('root_cause_validation_passed')}",
            "",
            "### Validation Failures",
        ])

        validation_failures = validation.get("validation_failures", [])
        if validation_failures:
            for failure in validation_failures:
                lines.append(f"- {failure}")
        else:
            lines.append("- None")

        lines.extend([
            "",
            "## Repair History",
            f"- Replans: {repair_history.get('replans')}",
        ])

        repair_events = repair_history.get("repair_events", [])
        if repair_events:
            lines.append("")
            lines.append("### Repair Events")
            for event in repair_events:
                lines.append(f"- {event}")
        else:
            lines.append("- No repair events were required.")

        warnings = repair_history.get("warnings", [])
        if warnings:
            lines.append("")
            lines.append("### Warnings")
            for warning in warnings:
                lines.append(f"- {warning}")

        lines.extend([
            "",
            "## Final Root Cause",
            f"- Root Cause: `{root_cause.get('root_cause')}`",
            f"- Confidence: {root_cause.get('confidence')}",
            f"- Summary: {root_cause.get('summary')}",
            "",
            "## Alternatives Considered",
        ])

        alternatives = report.get("alternatives_considered", [])
        if alternatives:
            for alternative in alternatives:
                lines.append(
                    f"- `{alternative.get('cause')}` "
                    f"confidence={alternative.get('confidence')}: "
                    f"{alternative.get('reason')}"
                )
        else:
            lines.append("- No alternative causes recorded.")

        lines.extend([
            "",
            "## Remediation Recommendation",
        ])

        if remediation:
            for key, value in remediation.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- No remediation recommendation produced.")

        lines.extend([
            "",
            "## Safety Notes",
        ])

        safety_notes = report.get("safety_notes", [])
        if safety_notes:
            for note in safety_notes:
                lines.append(f"- {note}")
        else:
            lines.append("- No safety notes recorded.")

        lines.append("")
        return "\n".join(lines)

    def _escape_markdown_table_text(self, value: object) -> str:
        if value is None:
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")

    def save_report(self, report: Dict) -> Path:
        report_id = report["report_id"]

        json_path = self.output_dir / f"{report_id}.json"
        markdown_path = self.output_dir / f"{report_id}.md"

        with json_path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2)

        with markdown_path.open("w", encoding="utf-8") as file:
            file.write(self._build_markdown_report(report))

        return json_path

    def _build_alert_context(self, state: PipelineState) -> Dict[str, Any]:
        alert = state.alert or {}

        return {
            "alert_id": state.alert_id,
            "model_id": state.model_id,
            "model_version": alert.get("model_version"),
            "environment": alert.get("environment"),
            "metric": alert.get("metric"),
            "current_value": alert.get("current_value"),
            "baseline_value": alert.get("baseline_value"),
            "severity": alert.get("severity"),
            "window_start": alert.get("window_start"),
            "window_end": alert.get("window_end"),
            "description": alert.get("description"),
            "metadata": alert.get("metadata", {}),
        }

    def _build_executive_summary(
        self,
        state: PipelineState,
        root_cause: Optional[Dict[str, Any]],
        remediation: Optional[Dict[str, Any]],
    ) -> str:
        alert = state.alert or {}
        metric = alert.get("metric", "monitored metric")
        severity = alert.get("severity", "unknown severity")

        if not root_cause:
            return (
                f"AegisML investigated {state.alert_id}, a {severity} production "
                f"ML alert on {metric}. The investigation completed but did not "
                "produce a confident root cause."
            )

        cause = root_cause.get("root_cause", "unknown")
        confidence = root_cause.get("confidence", "unknown")

        approval_text = (
            "Remediation requires human approval before production changes."
            if self._human_approval_required(remediation)
            else "No human-gated remediation recommendation was produced."
        )

        return (
            f"AegisML investigated {state.alert_id}, a {severity} production ML "
            f"alert on {metric}. The final root cause is {cause} with confidence "
            f"{confidence}. {approval_text}"
        )

    def _build_evidence_table(
        self,
        evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        table: List[Dict[str, Any]] = []

        for idx, item in enumerate(evidence, start=1):
            table.append(
                {
                    "evidence_id": idx,
                    "source": item.get("source"),
                    "supports": item.get("supports"),
                    "summary": item.get("summary") or item.get("finding"),
                    "details": item.get("details", {}) or item.get("metadata", {}),
                }
            )

        return table

    def _serialize_validation(self, validation: Dict) -> Dict:
        """
        plan_validation contains DiagnosticStep objects in approved_steps.
        Convert those to dictionaries for JSON serialization.
        """
        serialized = dict(validation)

        serialized["approved_steps"] = [
            step.model_dump()
            for step in validation.get("approved_steps", [])
        ]

        return serialized

    def _validation_passed(self, validation: Optional[Dict[str, Any]]) -> bool:
        if not validation:
            return False

        if "is_valid" in validation:
            return bool(validation["is_valid"])

        if "valid" in validation:
            return bool(validation["valid"])

        if "passed" in validation:
            return bool(validation["passed"])

        failures = validation.get("failures") or validation.get("errors") or []
        return len(failures) == 0

    def _collect_validation_failures(
        self,
        plan_validation: Dict[str, Any],
        root_cause_validation: Dict[str, Any],
    ) -> List[str]:
        failures: List[str] = []

        for key in ["issues", "failures", "errors", "missing_evidence"]:
            values = plan_validation.get(key, [])
            if isinstance(values, list):
                failures.extend(str(value) for value in values)

        for key in ["issues", "failures", "errors", "missing_evidence"]:
            values = root_cause_validation.get(key, [])
            if isinstance(values, list):
                failures.extend(str(value) for value in values)

        return failures

    def _human_approval_required(
        self,
        remediation: Optional[Dict[str, Any]],
    ) -> bool:
        if not remediation:
            return False

        return bool(remediation.get("human_approval_required", False))

    def _build_safety_notes(
        self,
        remediation: Optional[Dict[str, Any]],
    ) -> List[str]:
        notes = [
            "No remediation was executed automatically by AegisML.",
            "Diagnostic actions are read-only investigation steps.",
            "Production remediation remains human-gated.",
        ]

        if self._human_approval_required(remediation):
            notes.append(
                "Human approval is required before rollback, retraining, "
                "deployment, or production configuration changes."
            )

        return notes