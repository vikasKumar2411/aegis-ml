from typing import List

from app.services.json_data_service import JsonDataService
from app.state.pipeline_state import EvidenceItem


class DataQualityService:
    """
    Checks whether data-quality issues are present.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

    def run(self, model_id: str) -> List[EvidenceItem]:
        checks = self.data_service.get_data_quality(model_id)

        if not checks:
            return [
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-data-quality-missing",
                    source="data_quality_service",
                    finding="No data-quality results found.",
                    supports="missing_data_quality_evidence",
                    confidence=0.30,
                    metadata={"model_id": model_id},
                )
            ]

        issues = [row for row in checks if row.get("is_issue") is True]

        if issues:
            issue_names = [row.get("check_name") for row in issues]
            finding = f"Data-quality issues detected: {', '.join(issue_names)}."
            supports = "data_quality_issue_detected"
            confidence = 0.85
            metadata = {"issues": issues}
        else:
            finding = "No data-quality issues detected in monitored checks."
            supports = "data_quality_issue_excluded"
            confidence = 0.80
            metadata = {"checks": checks}

        return [
            EvidenceItem(
                evidence_id=f"EVID-{model_id}-data-quality",
                source="data_quality_service",
                finding=finding,
                supports=supports,
                confidence=confidence,
                metadata=metadata,
            )
        ]