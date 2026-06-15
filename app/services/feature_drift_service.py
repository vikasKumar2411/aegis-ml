from typing import List, Optional

from app.services.json_data_service import JsonDataService
from app.state.pipeline_state import EvidenceItem


class FeatureDriftService:
    """
    Checks whether input features show drift.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

    def run(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[EvidenceItem]:
        drift_rows = self.data_service.get_feature_drift(
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )
        evidence: List[EvidenceItem] = []

        if not drift_rows:
            return [
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-feature-drift-missing",
                    source="feature_drift_service",
                    finding="No feature drift results found.",
                    supports="missing_feature_drift_evidence",
                    confidence=0.30,
                    metadata={
                        "model_id": model_id,
                        "alert_id": alert_id,
                        "model_version": model_version,
                    },
                )
            ]

        drifted_features = [row for row in drift_rows if row.get("is_drifted")]

        if drifted_features:
            feature_names = [row.get("feature_name") for row in drifted_features]
            finding = f"Feature drift detected in: {', '.join(feature_names)}."
            supports = "feature_drift_detected"
            confidence = 0.85
            metadata = {
                "model_id": model_id,
                "alert_id": alert_id,
                "model_version": model_version,
                "drifted_features": drifted_features,
            }
        else:
            finding = "No significant feature drift detected."
            supports = "feature_drift_not_detected"
            confidence = 0.80
            metadata = {
                "model_id": model_id,
                "alert_id": alert_id,
                "model_version": model_version,
                "features_checked": drift_rows,
            }

        evidence.append(
            EvidenceItem(
                evidence_id=f"EVID-{model_id}-feature-drift",
                source="feature_drift_service",
                finding=finding,
                supports=supports,
                confidence=confidence,
                metadata=metadata,
            )
        )

        return evidence