from typing import Dict, List

from app.state.pipeline_state import DiagnosticStep


class PlannerAgent:
    """
    MVP planner agent.

    For v0.1 this is deterministic, but the interface is agent-shaped.
    Later we can replace the internals with an LLM planner while keeping
    the same contract.
    """

    def generate_plan(self, alert: Dict) -> List[DiagnosticStep]:
        metric = alert.get("metric", "")
        model_id = alert["model_id"]

        if "recall" in metric or "precision" in metric or "f1" in metric:
            return [
                DiagnosticStep(
                    step_id=1,
                    action="check_model_performance",
                    target=model_id,
                    reason="Confirm the model-performance degradation reported by the alert.",
                ),
                DiagnosticStep(
                    step_id=2,
                    action="analyze_prediction_errors",
                    target=model_id,
                    reason="Inspect false positives or false negatives to identify emerging error patterns.",
                ),
                DiagnosticStep(
                    step_id=3,
                    action="check_feature_drift",
                    target=model_id,
                    reason="Determine whether input feature distributions shifted during the alert window.",
                ),
                DiagnosticStep(
                    step_id=4,
                    action="check_recent_deployments",
                    target=model_id,
                    reason="Rule out a recent model or pipeline deployment as the cause of degradation.",
                ),
                DiagnosticStep(
                    step_id=5,
                    action="check_schema_drift",
                    target=model_id,
                    reason="Verify that the production input schema has not changed.",
                ),
                DiagnosticStep(
                    step_id=6,
                    action="check_data_quality",
                    target=model_id,
                    reason="Check whether upstream data-quality issues contributed to the alert.",
                ),
            ]

        return [
            DiagnosticStep(
                step_id=1,
                action="check_model_performance",
                target=model_id,
                reason="Run a default model-performance diagnostic check.",
            )
        ]