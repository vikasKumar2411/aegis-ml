from typing import Dict, List

from app.state.pipeline_state import DiagnosticStep


class PlanValidatorService:
    """
    Validates that a diagnostic plan is executable and safe.
    """

    VALID_ACTIONS = {
        "check_model_performance",
        "check_feature_drift",
        "analyze_prediction_errors",
        "check_recent_deployments",
        "check_schema_drift",
        "check_data_quality",
    }

    def validate(self, plan: List[DiagnosticStep]) -> Dict:
        invalid_reasons = []
        approved_steps = []

        seen_step_ids = set()

        for step in plan:
            if step.step_id in seen_step_ids:
                invalid_reasons.append(f"Duplicate step_id found: {step.step_id}")
                continue

            seen_step_ids.add(step.step_id)

            if step.action not in self.VALID_ACTIONS:
                invalid_reasons.append(f"Invalid action: {step.action}")
                continue

            if not step.target:
                invalid_reasons.append(f"Missing target for step_id: {step.step_id}")
                continue

            approved_steps.append(step)

        return {
            "is_valid": len(invalid_reasons) == 0,
            "approved_steps": approved_steps,
            "approved_step_count": len(approved_steps),
            "rejected_step_count": len(plan) - len(approved_steps),
            "invalid_reasons": invalid_reasons,
        }