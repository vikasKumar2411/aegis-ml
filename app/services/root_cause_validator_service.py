from typing import Dict, List

from app.state.pipeline_state import EvidenceItem, RootCause


class RootCauseValidatorService:
    """
    Validates whether a root-cause hypothesis is sufficiently supported
    by required diagnostic evidence.

    This is intentionally deterministic. It acts as a guardrail around
    root-cause reasoning and triggers adaptive evidence repair when
    required evidence is missing.
    """

    def validate(
        self,
        root_cause: RootCause,
        evidence: List[EvidenceItem],
    ) -> Dict:
        evidence_supports = {item.supports for item in evidence}

        missing_evidence = []
        feedback = []

        if root_cause is None:
            return {
                "is_valid": False,
                "feedback": ["Root cause is missing."],
                "missing_evidence": ["root_cause_hypothesis"],
                "evidence_supports": sorted(evidence_supports),
                "confidence": 0.0,
            }

        # Every valid incident root cause should have a confirmed performance drop,
        # except explicit false-alarm style outcomes.
        if root_cause.root_cause not in {"false_alarm", "inconclusive"}:
            if "model_performance_drop" not in evidence_supports:
                missing_evidence.append("model_performance_drop")
                feedback.append(
                    "Missing evidence confirming model-performance degradation."
                )

        required_by_root_cause = {
            "new_secure_email_patterns": {
                "new_secure_email_patterns": (
                    "Missing prediction-error evidence for new secure-email patterns."
                ),
                "deployment_issue_excluded": (
                    "Missing deployment exclusion evidence."
                ),
                "schema_drift_excluded": (
                    "Missing schema-drift exclusion evidence."
                ),
                "data_quality_issue_excluded": (
                    "Missing data-quality exclusion evidence."
                ),
            },
            "bad_model_deployment": {
                "bad_model_deployment_possible": (
                    "Missing evidence that a recent deployment correlates with the alert."
                ),
                "schema_drift_excluded": (
                    "Missing schema-drift exclusion evidence."
                ),
                "data_quality_issue_excluded": (
                    "Missing data-quality exclusion evidence."
                ),
            },
            "schema_drift": {
                "schema_drift_detected": (
                    "Missing positive schema-drift evidence."
                ),
                "deployment_issue_excluded": (
                    "Missing deployment exclusion evidence."
                ),
                "data_quality_issue_excluded": (
                    "Missing data-quality exclusion evidence."
                ),
            },
            "data_quality_issue": {
                "data_quality_issue_detected": (
                    "Missing positive data-quality issue evidence."
                ),
                "deployment_issue_excluded": (
                    "Missing deployment exclusion evidence."
                ),
                "schema_drift_excluded": (
                    "Missing schema-drift exclusion evidence."
                ),
            },
            "feature_drift": {
                "feature_drift_detected": (
                    "Missing positive feature-drift evidence."
                ),
                "deployment_issue_excluded": (
                    "Missing deployment exclusion evidence."
                ),
                "schema_drift_excluded": (
                    "Missing schema-drift exclusion evidence."
                ),
                "data_quality_issue_excluded": (
                    "Missing data-quality exclusion evidence."
                ),
            },
            "false_alarm": {
                "no_significant_model_performance_drop": (
                    "Missing evidence that the model-performance change is not significant."
                ),
                "deployment_issue_excluded": (
                    "Missing deployment exclusion evidence."
                ),
                "schema_drift_excluded": (
                    "Missing schema-drift exclusion evidence."
                ),
                "data_quality_issue_excluded": (
                    "Missing data-quality exclusion evidence."
                ),
            },
        }

        required = required_by_root_cause.get(root_cause.root_cause, {})

        for support_key, message in required.items():
            if support_key not in evidence_supports:
                missing_evidence.append(support_key)
                feedback.append(message)

        # If the root cause is inconclusive, inspect evidence gaps and request
        # follow-up diagnostics that could make the investigation conclusive.
        if root_cause.root_cause == "inconclusive":
            inconclusive_required = {
                "deployment_issue_excluded": (
                    "Root cause is inconclusive because deployment exclusion evidence is missing."
                ),
                "schema_drift_excluded": (
                    "Root cause is inconclusive because schema-drift exclusion evidence is missing."
                ),
                "data_quality_issue_excluded": (
                    "Root cause is inconclusive because data-quality exclusion evidence is missing."
                ),
            }

            for support_key, message in inconclusive_required.items():
                if support_key not in evidence_supports:
                    missing_evidence.append(support_key)
                    feedback.append(message)

        if root_cause.confidence < 0.7:
            feedback.append(
                f"Root-cause confidence {root_cause.confidence:.2f} is below threshold 0.70."
            )

        is_valid = len(missing_evidence) == 0 and root_cause.confidence >= 0.7

        return {
            "is_valid": is_valid,
            "feedback": feedback,
            "missing_evidence": missing_evidence,
            "evidence_supports": sorted(evidence_supports),
            "confidence": root_cause.confidence,
        }