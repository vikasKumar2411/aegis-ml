import json
from typing import Any, Dict, List

from app.services.llm_client import LLMClient
from app.state.pipeline_state import EvidenceItem, RootCause


class LLMRootCauseAgent:
    """
    LLM-backed root-cause synthesis agent.

    It converts deterministic diagnostic evidence into a root-cause hypothesis.
    The output is still checked by RootCauseValidatorService before acceptance.
    """

    def __init__(self) -> None:
        self.client = LLMClient()

    def infer(self, evidence: List[EvidenceItem]) -> RootCause:
        evidence_payload = [item.model_dump() for item in evidence]

        fallback = {
            "root_cause": "inconclusive",
            "confidence": 0.4,
            "summary": "The available evidence is insufficient to identify a confident root cause.",
            "alternative_causes": [],
        }

        result = self.client.generate_json(
            system_prompt=self._system_prompt(),
            user_prompt=json.dumps(
                {
                    "evidence": evidence_payload,
                    "allowed_root_causes": [
                        "new_secure_email_patterns",
                        "bad_model_deployment",
                        "schema_drift",
                        "data_quality_issue",
                        "feature_drift",
                        "mixed_cause",
                        "false_alarm",
                        "inconclusive",
                    ],
                    "required_output_schema": {
                        "root_cause": "string",
                        "confidence": "number between 0 and 1",
                        "summary": "string",
                        "alternative_causes": [
                            {
                                "cause": "string",
                                "confidence": "number between 0 and 1",
                                "reason": "string",
                            }
                        ],
                    },
                },
                indent=2,
            ),
            fallback=fallback,
        )

        root_cause = str(result.get("root_cause", "inconclusive"))

        # Normalize common LLM variants into our controlled taxonomy.
        root_cause = self._normalize_root_cause(root_cause)

        confidence = float(result.get("confidence", 0.4))
        confidence = max(0.0, min(confidence, 1.0))

        summary = str(
            result.get(
                "summary",
                "The available evidence is insufficient to identify a confident root cause.",
            )
        )

        alternative_causes = result.get("alternative_causes", [])
        if not isinstance(alternative_causes, list):
            alternative_causes = []

        return RootCause(
            root_cause=root_cause,
            confidence=confidence,
            summary=summary,
            alternative_causes=alternative_causes,
            metadata={
                "reasoning_mode": "llm",
                "llm_provider": result.get("_llm_provider"),
                "llm_model": result.get("_llm_model"),
                "used_fallback": result.get("_used_fallback", False),
                "llm_warning": result.get("_llm_warning"),
            },
        )

    def _system_prompt(self) -> str:
        return """
You are an ML incident root-cause synthesis agent.

You receive structured evidence from deterministic diagnostic tools.
Your job is to infer the most likely root cause.

Rules:
- Return ONLY valid JSON.
- Use one of the allowed root causes exactly.
- Prefer specific root causes over vague ones.
- If evidence shows false negatives with new secure-email phrasing, use new_secure_email_patterns.
- If evidence shows a correlated deployment, use bad_model_deployment.
- If evidence shows schema mismatch, use schema_drift.
- If evidence shows upstream data-quality degradation, use data_quality_issue.
- If evidence only shows feature distribution shift but no clearer cause, use feature_drift.
- If evidence supports multiple causes, use mixed_cause.
- If evidence is insufficient, use inconclusive.
- Do not recommend remediation here.
""".strip()

    def _normalize_root_cause(self, root_cause: str) -> str:
        normalized = root_cause.strip().lower().replace(" ", "_").replace("-", "_")

        mapping: Dict[str, str] = {
            "feature_drift_in_secure_phrase_count": "new_secure_email_patterns",
            "new_secure_email_phrasing": "new_secure_email_patterns",
            "new_secure_email_patterns": "new_secure_email_patterns",
            "bad_model_deployment": "bad_model_deployment",
            "deployment_issue": "bad_model_deployment",
            "schema_drift": "schema_drift",
            "data_quality_issue": "data_quality_issue",
            "feature_drift": "feature_drift",
            "mixed_cause": "mixed_cause",
            "false_alarm": "false_alarm",
            "inconclusive": "inconclusive",
        }

        return mapping.get(normalized, "inconclusive")
