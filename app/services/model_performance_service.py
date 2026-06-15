from typing import List, Optional

from app.services.json_data_service import JsonDataService
from app.state.pipeline_state import EvidenceItem


class ModelPerformanceService:
    """
    Checks whether the alerted model metric has degraded.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

    def run(
        self,
        model_id: str,
        alert_metric: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[EvidenceItem]:
        metrics = self.data_service.get_model_metrics(
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )
        evidence: List[EvidenceItem] = []

        for row in metrics:
            metric = row.get("metric")

            if metric != alert_metric:
                continue

            baseline = row.get("baseline_value")
            current = row.get("current_value")
            drop = row.get("drop")
            is_significant = row.get("is_significant", False)

            if drop is None and baseline is not None and current is not None:
                drop = round(float(baseline) - float(current), 4)

            if is_significant:
                finding = (
                    f"{metric} dropped from {baseline} to {current}, "
                    f"a decline of {drop}."
                )
                supports = "model_performance_drop"
                confidence = 0.95
            else:
                finding = (
                    f"{metric} changed from {baseline} to {current}, "
                    "but the change is not significant."
                )
                supports = "no_significant_model_performance_drop"
                confidence = 0.70

            evidence.append(
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-{metric}",
                    source="model_performance_service",
                    finding=finding,
                    supports=supports,
                    confidence=confidence,
                    metadata={
                        **row,
                        "alert_id": alert_id,
                        "model_version": model_version or row.get("model_version"),
                    },
                )
            )

        if not evidence:
            evidence.append(
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-metric-not-found",
                    source="model_performance_service",
                    finding=f"No metric record found for {alert_metric}.",
                    supports="missing_model_performance_evidence",
                    confidence=0.30,
                    metadata={
                        "model_id": model_id,
                        "metric": alert_metric,
                        "alert_id": alert_id,
                        "model_version": model_version,
                    },
                )
            )

        return evidence