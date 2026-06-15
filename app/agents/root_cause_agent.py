from typing import List, Set

from app.state.pipeline_state import EvidenceItem, RootCause


class RootCauseAgent:
    """
    MVP root-cause agent.

    For v0.1 this uses evidence-based rules. Later this can become an LLM
    synthesis agent while preserving the same input/output contract.
    """

    def infer(self, evidence: List[EvidenceItem]) -> RootCause:
        supports: Set[str] = {item.supports for item in evidence}

        if self._supports_new_secure_pattern_cause(supports):
            return RootCause(
                root_cause="new_secure_email_patterns",
                confidence=0.85,
                summary=(
                    "The model performance drop is most likely caused by new secure-email "
                    "language patterns. Evidence shows a significant recall drop, false "
                    "negatives with new secure phrasing, feature drift in secure phrase count, "
                    "and no correlated deployment issue."
                ),
                alternative_causes=[
                    {
                        "cause": "bad_model_deployment",
                        "confidence": 0.10,
                        "reason": "Deployment correlation was checked and no correlated deployment event was found.",
                    },
                    {
                        "cause": "schema_drift",
                        "confidence": 0.03,
                        "reason": "Schema drift was checked and excluded.",
                    },
                    {
                        "cause": "data_quality_issue",
                        "confidence": 0.02,
                        "reason": "Data-quality checks did not show degradation.",
                    },
                ],
                metadata={"reasoning_mode": "deterministic"},
            )

        if "bad_model_deployment_possible" in supports:
            return RootCause(
                root_cause="bad_model_deployment",
                confidence=0.80,
                summary=(
                    "A deployment event appears correlated with the model degradation. "
                    "The likely cause is a bad model or pipeline deployment."
                ),
                alternative_causes=[
                    {
                        "cause": "feature_drift",
                        "confidence": 0.20,
                        "reason": "Feature drift may contribute but deployment correlation is stronger.",
                    }
                ],
                metadata={"reasoning_mode": "deterministic"},
            )

        if "schema_drift_detected" in supports:
            return RootCause(
                root_cause="schema_drift",
                confidence=0.85,
                summary=(
                    "The model degradation is likely caused by input schema drift, "
                    "because required fields changed or went missing."
                ),
                alternative_causes=[],
                metadata={"reasoning_mode": "deterministic"},
            )

        if "data_quality_issue_detected" in supports:
            return RootCause(
                root_cause="data_quality_issue",
                confidence=0.80,
                summary=(
                    "The model degradation is likely caused by upstream data-quality issues."
                ),
                alternative_causes=[],
                metadata={"reasoning_mode": "deterministic"},
            )

        if self._supports_feature_drift_cause(supports):
            return RootCause(
                root_cause="feature_drift",
                confidence=0.82,
                summary=(
                    "The model degradation is most likely caused by feature drift. "
                    "Evidence shows a significant model-performance drop and detected "
                    "input feature distribution shift, while deployment, schema drift, "
                    "and upstream data-quality issues were excluded."
                ),
                alternative_causes=[
                    {
                        "cause": "bad_model_deployment",
                        "confidence": 0.08,
                        "reason": "Deployment diagnostics were checked and excluded.",
                    },
                    {
                        "cause": "schema_drift",
                        "confidence": 0.05,
                        "reason": "Schema drift diagnostics were checked and excluded.",
                    },
                    {
                        "cause": "data_quality_issue",
                        "confidence": 0.05,
                        "reason": "Data-quality diagnostics were checked and excluded.",
                    },
                ],
                metadata={"reasoning_mode": "deterministic"},
            )

        if "no_significant_model_performance_drop" in supports:
            return RootCause(
                root_cause="false_alarm",
                confidence=0.85,
                summary=(
                    "The alert appears to be a false alarm because the monitored metric "
                    "changed only slightly and did not show a significant performance degradation."
                ),
                alternative_causes=[
                    {
                        "cause": "minor_metric_noise",
                        "confidence": 0.70,
                        "reason": "The metric movement is within the expected non-significant range.",
                    }
                ],
                metadata={"reasoning_mode": "deterministic"},
            )

        return RootCause(
            root_cause="inconclusive",
            confidence=0.40,
            summary=(
                "The available evidence is insufficient to identify a confident root cause."
            ),
            alternative_causes=[
                {
                    "cause": "unknown",
                    "confidence": 0.60,
                    "reason": "Required diagnostic evidence is missing or contradictory.",
                }
            ],
            metadata={"reasoning_mode": "deterministic"},
        )

    def _supports_new_secure_pattern_cause(self, supports: Set[str]) -> bool:
        required = {
            "model_performance_drop",
            "new_secure_email_patterns",
            "deployment_issue_excluded",
        }
        return required.issubset(supports)

    def _supports_feature_drift_cause(self, supports: Set[str]) -> bool:
        required = {
            "model_performance_drop",
            "feature_drift_detected",
            "deployment_issue_excluded",
            "schema_drift_excluded",
            "data_quality_issue_excluded",
        }
        return required.issubset(supports)