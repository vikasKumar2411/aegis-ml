from typing import Dict, List, Set

from app.state.pipeline_state import EvidenceItem, RootCause


class RootCauseValidatorService:
    """
    Validates whether the inferred root cause has enough supporting evidence.

    This is a key guardrail: the root-cause agent cannot simply assert a cause
    without required evidence.
    """

    REQUIRED_EVIDENCE = {
        "new_secure_email_patterns": {
            "model_performance_drop",
            "new_secure_email_patterns",
            "deployment_issue_excluded",
        },
        "bad_model_deployment": {
            "model_performance_drop",
            "bad_model_deployment_possible",
        },
        "schema_drift": {
            "model_performance_drop",
            "schema_drift_detected",
        },
        "data_quality_issue": {
            "model_performance_drop",
            "data_quality_issue_detected",
        },
    }

    def validate(
        self,
        root_cause: RootCause,
        evidence: List[EvidenceItem],
    ) -> Dict:
        supports: Set[str] = {item.supports for item in evidence}
        required = self.REQUIRED_EVIDENCE.get(root_cause.root_cause, set())

        missing = sorted(required - supports)

        is_valid = len(missing) == 0 and root_cause.confidence >= 0.70

        return {
            "is_valid": is_valid,
            "root_cause": root_cause.root_cause,
            "confidence": root_cause.confidence,
            "required_evidence": sorted(required),
            "available_evidence": sorted(supports),
            "missing_evidence": missing,
            "feedback": self._build_feedback(root_cause.root_cause, missing),
        }

    def _build_feedback(self, root_cause: str, missing: List[str]) -> List[str]:
        if not missing:
            return []

        return [
            f"Root cause '{root_cause}' is missing required evidence: {item}"
            for item in missing
        ]