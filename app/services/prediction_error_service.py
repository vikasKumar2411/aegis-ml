from collections import Counter
from typing import List

from app.services.json_data_service import JsonDataService
from app.state.pipeline_state import EvidenceItem


class PredictionErrorService:
    """
    Analyzes prediction errors, especially false negatives.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

    def run(self, model_id: str) -> List[EvidenceItem]:
        samples = self.data_service.get_prediction_samples(model_id)

        if not samples:
            return [
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-prediction-errors-missing",
                    source="prediction_error_service",
                    finding="No prediction error samples found.",
                    supports="missing_prediction_error_evidence",
                    confidence=0.30,
                    metadata={"model_id": model_id},
                )
            ]

        false_negatives = [
            row for row in samples if row.get("error_type") == "false_negative"
        ]

        pattern_counts = Counter(
            row.get("pattern", "unknown_pattern") for row in false_negatives
        )

        if false_negatives and pattern_counts:
            dominant_pattern, count = pattern_counts.most_common(1)[0]
            finding = (
                f"{count} false-negative samples share dominant pattern: "
                f"{dominant_pattern}."
            )
            supports = dominant_pattern
            confidence = 0.90
        else:
            finding = "No strong false-negative error pattern detected."
            supports = "no_clear_prediction_error_pattern"
            confidence = 0.60

        return [
            EvidenceItem(
                evidence_id=f"EVID-{model_id}-prediction-errors",
                source="prediction_error_service",
                finding=finding,
                supports=supports,
                confidence=confidence,
                metadata={
                    "false_negative_count": len(false_negatives),
                    "pattern_counts": dict(pattern_counts),
                    "samples": samples,
                },
            )
        ]