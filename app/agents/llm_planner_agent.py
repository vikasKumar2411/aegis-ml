import json
from typing import Any, Dict, List

from app.agents.planner_agent import PlannerAgent
from app.services.llm_client import LLMClient
from app.state.pipeline_state import DiagnosticStep


class LLMPlannerAgent:
    """
    LLM-backed diagnostic planner.

    Produces a candidate investigation plan from an alert and allowed actions.
    The deterministic plan critic and validator still review the plan before
    execution.
    """

    def __init__(self, simulate_incomplete_plan: bool = False) -> None:
        self.client = LLMClient()
        self.fallback_planner = PlannerAgent(
            simulate_incomplete_plan=simulate_incomplete_plan
        )
        self.simulate_incomplete_plan = simulate_incomplete_plan

    def generate_plan(self, alert: Dict[str, Any]) -> List[DiagnosticStep]:
        fallback_steps = self.fallback_planner.generate_plan(alert)

        fallback_payload = {
            "steps": [step.model_dump() for step in fallback_steps],
            "_used_fallback": True,
        }

        result = self.client.generate_json(
            system_prompt=self._system_prompt(),
            user_prompt=json.dumps(
                {
                    "alert": alert,
                    "allowed_actions": [
                        "check_model_performance",
                        "analyze_prediction_errors",
                        "check_feature_drift",
                        "check_recent_deployments",
                        "check_schema_drift",
                        "check_data_quality",
                    ],
                    "required_output_schema": {
                        "steps": [
                            {
                                "step_id": "integer",
                                "action": "one of allowed_actions",
                                "target": "model id or relevant target",
                                "reason": "short reason for this diagnostic step",
                            }
                        ]
                    },
                },
                indent=2,
            ),
            fallback=fallback_payload,
        )

        raw_steps = result.get("steps", [])

        if not isinstance(raw_steps, list):
            return fallback_steps

        parsed_steps: List[DiagnosticStep] = []

        for idx, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue

            action = str(step.get("action", "")).strip()
            target = str(step.get("target", alert.get("model_id", ""))).strip()
            reason = str(step.get("reason", "LLM-selected diagnostic step.")).strip()

            if not action:
                continue

            parsed_steps.append(
                DiagnosticStep(
                    step_id=idx,
                    action=action,
                    target=target,
                    reason=reason,
                )
            )

        if not parsed_steps:
            return fallback_steps

        if self.simulate_incomplete_plan:
            parsed_steps = [
                step
                for step in parsed_steps
                if step.action != "check_recent_deployments"
            ]

        return parsed_steps

    def _system_prompt(self) -> str:
        return """
You are an ML incident diagnostic planning agent.

Your job is to create a short, high-quality diagnostic plan for a production ML alert.

Rules:
- Return ONLY valid JSON.
- Use only allowed actions.
- Do not invent tools.
- Prefer 4 to 6 diagnostic steps.
- Always include check_model_performance for model metric degradation.
- Include analyze_prediction_errors when recall, precision, false positives, or false negatives are involved.
- Include check_feature_drift when behavior may have changed due to input distribution shift.
- Include check_recent_deployments to rule out deployment-caused regressions.
- Include check_schema_drift to rule out input contract changes.
- Include check_data_quality to rule out upstream quality problems.
- Each step must have step_id, action, target, and reason.
""".strip()