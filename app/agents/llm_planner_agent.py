import json
from typing import Any, Dict, List, Set

from app.agents.planner_agent import PlannerAgent
from app.services.llm_client import LLMClient
from app.state.pipeline_state import DiagnosticStep


class LLMPlannerAgent:
    """
    LLM-backed diagnostic planner.

    Produces a candidate investigation plan from an alert and allowed actions.
    The deterministic plan critic and validator still review the plan before
    execution.

    Important design principle:
    - The LLM can propose the diagnostic strategy.
    - Deterministic post-processing enforces allowed actions and baseline
      production ML diagnostics.
    """

    ALLOWED_ACTIONS: Set[str] = {
        "check_model_performance",
        "analyze_prediction_errors",
        "check_feature_drift",
        "check_recent_deployments",
        "check_schema_drift",
        "check_data_quality",
    }

    BASELINE_ACTIONS: List[str] = [
        "check_model_performance",
        "analyze_prediction_errors",
        "check_recent_deployments",
        "check_schema_drift",
        "check_data_quality",
    ]

    FEATURE_DRIFT_TRIGGERS = [
        "recall",
        "precision",
        "false positive",
        "false negative",
        "metric",
        "performance",
        "degradation",
        "drift",
        "distribution",
        "prediction",
        "pattern",
        "secure email",
    ]

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
                    "allowed_actions": sorted(self.ALLOWED_ACTIONS),
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
            parsed_steps = fallback_steps
        else:
            parsed_steps = self._parse_llm_steps(
                raw_steps=raw_steps,
                alert=alert,
            )

        if not parsed_steps:
            parsed_steps = fallback_steps

        parsed_steps = self._complete_with_baseline(
            steps=parsed_steps,
            alert=alert,
        )

        if self.simulate_incomplete_plan:
            parsed_steps = self._simulate_incomplete_plan(parsed_steps)

        return self._renumber_steps(parsed_steps)

    def _parse_llm_steps(
        self,
        raw_steps: List[Any],
        alert: Dict[str, Any],
    ) -> List[DiagnosticStep]:
        parsed_steps: List[DiagnosticStep] = []

        for idx, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue

            action = str(step.get("action", "")).strip()
            target = str(step.get("target", alert.get("model_id", ""))).strip()
            reason = str(
                step.get("reason", "LLM-selected diagnostic step.")
            ).strip()

            if action not in self.ALLOWED_ACTIONS:
                continue

            parsed_steps.append(
                DiagnosticStep(
                    step_id=idx,
                    action=action,
                    target=target,
                    reason=reason,
                )
            )

        return self._dedupe_steps(parsed_steps)

    def _complete_with_baseline(
        self,
        steps: List[DiagnosticStep],
        alert: Dict[str, Any],
    ) -> List[DiagnosticStep]:
        """
        Ensures the LLM plan has the minimum production ML incident baseline.

        This is intentionally deterministic. The LLM proposes, but production
        incident safety requires deployment, schema, and data-quality causes to
        be ruled out before root-cause synthesis.
        """
        completed_steps = list(steps)
        existing_actions = {step.action for step in completed_steps}

        target = str(alert.get("model_id", "production_ml_model"))

        for action in self.BASELINE_ACTIONS:
            if action not in existing_actions:
                completed_steps.append(
                    DiagnosticStep(
                        step_id=len(completed_steps) + 1,
                        action=action,
                        target=target,
                        reason=self._baseline_reason(action),
                    )
                )
                existing_actions.add(action)

        if (
            self._should_include_feature_drift(alert)
            and "check_feature_drift" not in existing_actions
        ):
            completed_steps.append(
                DiagnosticStep(
                    step_id=len(completed_steps) + 1,
                    action="check_feature_drift",
                    target=target,
                    reason=(
                        "Baseline production ML diagnostic to check whether "
                        "input distribution shift explains the observed metric "
                        "or prediction-pattern change."
                    ),
                )
            )

        return self._dedupe_steps(completed_steps)

    def _should_include_feature_drift(self, alert: Dict[str, Any]) -> bool:
        alert_text = json.dumps(alert).lower()
        return any(
            trigger in alert_text
            for trigger in self.FEATURE_DRIFT_TRIGGERS
        )

    def _baseline_reason(self, action: str) -> str:
        reasons = {
            "check_model_performance": (
                "Baseline production ML diagnostic to confirm the metric "
                "movement and quantify severity."
            ),
            "analyze_prediction_errors": (
                "Baseline production ML diagnostic to inspect false positives, "
                "false negatives, and changed prediction patterns."
            ),
            "check_recent_deployments": (
                "Baseline production ML diagnostic to rule out a deployment "
                "or model-release regression."
            ),
            "check_schema_drift": (
                "Baseline production ML diagnostic to rule out upstream input "
                "contract or field-level schema changes."
            ),
            "check_data_quality": (
                "Baseline production ML diagnostic to rule out nulls, malformed "
                "records, missing fields, or upstream data-quality issues."
            ),
        }

        return reasons.get(
            action,
            "Baseline production ML diagnostic required for safe investigation.",
        )

    def _simulate_incomplete_plan(
        self,
        steps: List[DiagnosticStep],
    ) -> List[DiagnosticStep]:
        """
        Used only by repair-stress eval cases.

        This intentionally removes diagnostics so the validator/repair loop
        must recover them.
        """
        removed_actions = {
            "check_recent_deployments",
            "check_schema_drift",
            "check_data_quality",
        }

        return [
            step
            for step in steps
            if step.action not in removed_actions
        ]

    def _dedupe_steps(
        self,
        steps: List[DiagnosticStep],
    ) -> List[DiagnosticStep]:
        deduped: List[DiagnosticStep] = []
        seen_actions: Set[str] = set()

        for step in steps:
            if step.action in seen_actions:
                continue

            deduped.append(step)
            seen_actions.add(step.action)

        return self._renumber_steps(deduped)

    def _renumber_steps(
        self,
        steps: List[DiagnosticStep],
    ) -> List[DiagnosticStep]:
        renumbered_steps: List[DiagnosticStep] = []

        for idx, step in enumerate(steps, start=1):
            renumbered_steps.append(
                DiagnosticStep(
                    step_id=idx,
                    action=step.action,
                    target=step.target,
                    reason=step.reason,
                )
            )

        return renumbered_steps

    def _system_prompt(self) -> str:
        return """
You are an ML incident diagnostic planning agent.

Your job is to create a high-quality diagnostic plan for a production ML alert.

Rules:
- Return ONLY valid JSON.
- Use only allowed actions.
- Do not invent tools.
- Prefer 5 to 6 diagnostic steps for production ML incidents.
- Do not stop after only 2 or 3 checks.
- Production ML incidents require ruling out model-performance, prediction-error, deployment, schema, data-quality, and feature-distribution causes before root-cause synthesis.
- Always include check_model_performance for model metric degradation.
- Include analyze_prediction_errors when recall, precision, false positives, or false negatives are involved.
- Include check_recent_deployments to rule out deployment-caused regressions.
- Include check_schema_drift to rule out input contract changes.
- Include check_data_quality to rule out upstream quality problems.
- Include check_feature_drift when behavior may have changed due to input distribution shift, new language patterns, recall degradation, precision degradation, or unexplained metric movement.
- Each step must have step_id, action, target, and reason.

Return JSON with this shape:
{
  "steps": [
    {
      "step_id": 1,
      "action": "check_model_performance",
      "target": "model id or relevant target",
      "reason": "why this diagnostic is needed"
    }
  ]
}
""".strip()