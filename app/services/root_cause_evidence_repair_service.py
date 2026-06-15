from typing import Dict, List

from app.state.pipeline_state import DiagnosticStep, PipelineState


class RootCauseEvidenceRepairService:
    """
    Builds follow-up diagnostic steps when root-cause validation detects
    missing evidence.

    This is the adaptive repair/replanning layer.
    """

    EVIDENCE_TO_ACTION = {
        # Performance evidence
        "model_performance_drop": "check_model_performance",
        "no_significant_model_performance_drop": "check_model_performance",

        # Prediction-error evidence
        "new_secure_email_patterns": "analyze_prediction_errors",
        "post_deployment_false_positive": "analyze_prediction_errors",
        "missing_body_field": "analyze_prediction_errors",
        "empty_body_due_to_data_quality": "analyze_prediction_errors",
        "no_clear_prediction_error_pattern": "analyze_prediction_errors",

        # Deployment evidence
        "bad_model_deployment_possible": "check_recent_deployments",
        "deployment_issue_excluded": "check_recent_deployments",

        # Schema evidence
        "schema_drift_detected": "check_schema_drift",
        "schema_drift_excluded": "check_schema_drift",

        # Data-quality evidence
        "data_quality_issue_detected": "check_data_quality",
        "data_quality_issue_excluded": "check_data_quality",

        # Feature-drift evidence
        "feature_drift_detected": "check_feature_drift",
        "feature_drift_not_detected": "check_feature_drift",
    }

    ACTION_REASON = {
        "check_model_performance": (
            "Root-cause validation requires model-performance evidence before "
            "accepting the hypothesis."
        ),
        "analyze_prediction_errors": (
            "Root-cause validation requires prediction-error evidence before "
            "accepting the hypothesis."
        ),
        "check_recent_deployments": (
            "Root-cause validation requires deployment evidence before accepting "
            "the hypothesis."
        ),
        "check_schema_drift": (
            "Root-cause validation requires schema-drift evidence before accepting "
            "the hypothesis."
        ),
        "check_data_quality": (
            "Root-cause validation requires data-quality evidence before accepting "
            "the hypothesis."
        ),
        "check_feature_drift": (
            "Root-cause validation requires feature-drift evidence before accepting "
            "the hypothesis."
        ),
    }

    def build_repair_plan(
        self,
        state: PipelineState,
        root_cause_validation: Dict,
    ) -> List[DiagnosticStep]:
        missing_evidence = root_cause_validation.get("missing_evidence", [])

        existing_actions = {step.action for step in state.plan}
        repair_steps: List[DiagnosticStep] = []

        next_step_id = max([step.step_id for step in state.plan], default=0) + 1

        for evidence_key in missing_evidence:
            action = self.EVIDENCE_TO_ACTION.get(evidence_key)

            if action is None:
                state.add_warning(
                    f"No repair action mapping found for missing evidence: {evidence_key}"
                )
                continue

            if action in existing_actions:
                continue

            repair_steps.append(
                DiagnosticStep(
                    step_id=next_step_id,
                    action=action,
                    target=state.model_id,
                    reason=self.ACTION_REASON.get(
                        action,
                        "Root-cause validation requires additional diagnostic evidence.",
                    ),
                )
            )

            existing_actions.add(action)
            next_step_id += 1

        return repair_steps