from typing import List

from app.services.json_data_service import JsonDataService
from app.state.pipeline_state import EvidenceItem


class SchemaDriftService:
    """
    Checks whether the input schema changed.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

    def run(self, model_id: str) -> List[EvidenceItem]:
        profile = self.data_service.get_schema_profile(model_id)

        if not profile:
            return [
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-schema-missing",
                    source="schema_drift_service",
                    finding="No schema profile found.",
                    supports="missing_schema_evidence",
                    confidence=0.30,
                    metadata={"model_id": model_id},
                )
            ]

        if profile.get("schema_drift_detected"):
            finding = (
                "Schema drift detected. "
                f"Missing fields: {profile.get('missing_fields', [])}. "
                f"Extra fields: {profile.get('extra_fields', [])}."
            )
            supports = "schema_drift_detected"
            confidence = 0.90
        else:
            finding = "No schema drift detected; expected and observed fields match."
            supports = "schema_drift_excluded"
            confidence = 0.85

        return [
            EvidenceItem(
                evidence_id=f"EVID-{model_id}-schema-drift",
                source="schema_drift_service",
                finding=finding,
                supports=supports,
                confidence=confidence,
                metadata=profile,
            )
        ]