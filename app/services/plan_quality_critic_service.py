from typing import Dict, List

from app.state.pipeline_state import DiagnosticStep


class PlanQualityCriticService:
    """
    Critiques whether the diagnostic plan is sufficient for the alert type.

    This is intentionally separate from validation:
    - Validator asks: can we execute this plan?
    - Critic asks: is this plan good enough?
    """

    def critique(self, alert: Dict, plan: List[DiagnosticStep]) -> Dict:
        metric = alert.get("metric", "")
        actions = {step.action for step in plan}
        feedback = []

        if "recall" in metric or "precision" in metric or "f1" in metric:
            required_actions = {
                "check_model_performance",
                "analyze_prediction_errors",
                "check_recent_deployments",
            }

            missing = required_actions - actions
            for action in sorted(missing):
                feedback.append(
                    f"Model-performance degradation plan should include {action}."
                )

        if "schema" in metric and "check_schema_drift" not in actions:
            feedback.append("Schema-related alert should include check_schema_drift.")

        return {
            "is_sufficient": len(feedback) == 0,
            "feedback": feedback,
        }