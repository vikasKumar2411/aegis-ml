import json
from pathlib import Path
from typing import Dict

from app.state.pipeline_state import PipelineState


class FinalReportService:
    """
    Builds and saves the final AegisML investigation report.
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

        report = {
            "report_id": report_id,
            "alert_id": state.alert_id,
            "model_id": state.model_id,
            "goal": state.goal,
            "alert": state.alert,
            "plan": [step.model_dump() for step in state.plan],
            "plan_quality": plan_quality,
            "plan_validation": self._serialize_validation(plan_validation),
            "completed_steps": state.completed_steps,
            "evidence": [item.model_dump() for item in state.evidence],
            "root_cause": (
                state.root_cause.model_dump() if state.root_cause else None
            ),
            "root_cause_validation": root_cause_validation,
            "remediation": (
                state.remediation.model_dump() if state.remediation else None
            ),
            "warnings": state.warnings,
            "errors": state.errors,
            "replans": state.replans,
        }

        state.final_report = report
        return report

    def save_report(self, report: Dict) -> Path:
        report_id = report["report_id"]
        path = self.output_dir / f"{report_id}.json"

        with path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2)

        return path

    def _serialize_validation(self, validation: Dict) -> Dict:
        """
        plan_validation contains DiagnosticStep objects in approved_steps.
        Convert those to dictionaries for JSON serialization.
        """
        serialized = dict(validation)
        serialized["approved_steps"] = [
            step.model_dump() for step in validation.get("approved_steps", [])
        ]
        return serialized