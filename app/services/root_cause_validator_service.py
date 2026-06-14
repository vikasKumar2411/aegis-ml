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
            }

        # Every valid incident root cause should have a confirmed performance drop.
        if "model_performance_drop" not in evidence_supports:
            missing_evidence.append("model_performance_drop")
            feedback.append("Missing evidence confirming model-performance degradation.")

        # For new secure-email pattern root cause, require positive pattern evidence
        # and exclusionary evidence for common competing causes.
        if root_cause.root_cause == "new_secure_email_patterns":
            required = {
                "new_secure_email_patterns": "Missing prediction-error evidence for new secure-email patterns.",
                "deployment_issue_excluded": "Missing deployment exclusion evidence.",
                "schema_drift_excluded": "Missing schema-drift exclusion evidence.",
                "data_quality_issue_excluded": "Missing data-quality exclusion evidence.",
            }

            for support_key, message in required.items():
                if support_key not in evidence_supports:
                    missing_evidence.append(support_key)
                    feedback.append(message)

        # If the root cause is inconclusive, inspect evidence gaps and request
        # follow-up diagnostics that could make the investigation conclusive.
        if root_cause.root_cause == "inconclusive":
            if "deployment_issue_excluded" not in evidence_supports:
                missing_evidence.append("deployment_issue_excluded")
                feedback.append(
                    "Root cause is inconclusive because deployment exclusion evidence is missing."
                )

            if "schema_drift_excluded" not in evidence_supports:
                missing_evidence.append("schema_drift_excluded")
                feedback.append(
                    "Root cause is inconclusive because schema-drift exclusion evidence is missing."
                )

            if "data_quality_issue_excluded" not in evidence_supports:
                missing_evidence.append("data_quality_issue_excluded")
                feedback.append(
                    "Root cause is inconclusive because data-quality exclusion evidence is missing."
                )

        is_valid = len(missing_evidence) == 0 and root_cause.confidence >= 0.7

        if root_cause.confidence < 0.7:
            feedback.append(
                f"Root-cause confidence {root_cause.confidence:.2f} is below threshold 0.70."
            )

        return {
            "is_valid": is_valid,
            "feedback": feedback,
            "missing_evidence": missing_evidence,
            "evidence_supports": sorted(evidence_supports),
            "confidence": root_cause.confidence,
        }