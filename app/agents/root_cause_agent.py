from typing import Dict, List, Set

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
            )

        if "data_quality_issue_detected" in supports:
            return RootCause(
                root_cause="data_quality_issue",
                confidence=0.80,
                summary=(
                    "The model degradation is likely caused by upstream data-quality issues."
                ),
                alternative_causes=[],
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
        )

    def _supports_new_secure_pattern_cause(self, supports: Set[str]) -> bool:
        required = {
            "model_performance_drop",
            "new_secure_email_patterns",
            "deployment_issue_excluded",
        }
        return required.issubset(supports)