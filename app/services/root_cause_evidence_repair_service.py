from typing import Dict, List

from app.state.pipeline_state import DiagnosticStep, PipelineState


class RootCauseEvidenceRepairService:
    """
    Builds follow-up diagnostic steps when root-cause validation detects
    missing evidence.

    This is the adaptive repair/replanning layer.
    """

    def build_repair_plan(
        self,
        state: PipelineState,
        root_cause_validation: Dict,
    ) -> List[DiagnosticStep]:
        missing_evidence = root_cause_validation.get("missing_evidence", [])

        existing_actions = {step.action for step in state.plan}
        repair_steps: List[DiagnosticStep] = []

        next_step_id = max([step.step_id for step in state.plan], default=0) + 1

        if (
            "deployment_issue_excluded" in missing_evidence
            and "check_recent_deployments" not in existing_actions
        ):
            repair_steps.append(
                DiagnosticStep(
                    step_id=next_step_id,
                    action="check_recent_deployments",
                    target=state.model_id,
                    reason=(
                        "Root-cause validation requires deployment exclusion "
                        "evidence before accepting the hypothesis."
                    ),
                )
            )
            next_step_id += 1

        if (
            "schema_drift_excluded" in missing_evidence
            and "check_schema_drift" not in existing_actions
        ):
            repair_steps.append(
                DiagnosticStep(
                    step_id=next_step_id,
                    action="check_schema_drift",
                    target=state.model_id,
                    reason=(
                        "Root-cause validation requires schema-drift exclusion "
                        "evidence before accepting the hypothesis."
                    ),
                )
            )
            next_step_id += 1

        if (
            "data_quality_issue_excluded" in missing_evidence
            and "check_data_quality" not in existing_actions
        ):
            repair_steps.append(
                DiagnosticStep(
                    step_id=next_step_id,
                    action="check_data_quality",
                    target=state.model_id,
                    reason=(
                        "Root-cause validation requires data-quality exclusion "
                        "evidence before accepting the hypothesis."
                    ),
                )
            )
            next_step_id += 1

        if (
            "model_performance_drop" in missing_evidence
            and "check_model_performance" not in existing_actions
        ):
            repair_steps.append(
                DiagnosticStep(
                    step_id=next_step_id,
                    action="check_model_performance",
                    target=state.model_id,
                    reason=(
                        "Root-cause validation requires confirmed model-performance "
                        "degradation evidence."
                    ),
                )
            )
            next_step_id += 1

        if (
            "new_secure_email_patterns" in missing_evidence
            and "analyze_prediction_errors" not in existing_actions
        ):
            repair_steps.append(
                DiagnosticStep(
                    step_id=next_step_id,
                    action="analyze_prediction_errors",
                    target=state.model_id,
                    reason=(
                        "Root-cause validation requires prediction-error evidence "
                        "for new secure-email patterns."
                    ),
                )
            )

        return repair_steps