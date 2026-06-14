from typing import List

from app.services.json_data_service import JsonDataService
from app.state.pipeline_state import EvidenceItem


class DeploymentService:
    """
    Checks whether a recent deployment correlates with the alert.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

    def run(self, model_id: str) -> List[EvidenceItem]:
        deployments = self.data_service.get_deployments(model_id)

        if not deployments:
            return [
                EvidenceItem(
                    evidence_id=f"EVID-{model_id}-deployments-missing",
                    source="deployment_service",
                    finding="No deployment events found.",
                    supports="missing_deployment_evidence",
                    confidence=0.40,
                    metadata={"model_id": model_id},
                )
            ]

        correlated = [
            row for row in deployments if row.get("correlates_with_alert") is True
        ]

        if correlated:
            finding = "At least one deployment correlates with the alert window."
            supports = "bad_model_deployment_possible"
            confidence = 0.80
            metadata = {"correlated_deployments": correlated}
        else:
            finding = "No deployment event appears correlated with the alert window."
            supports = "deployment_issue_excluded"
            confidence = 0.85
            metadata = {"deployments_checked": deployments}

        return [
            EvidenceItem(
                evidence_id=f"EVID-{model_id}-deployment-correlation",
                source="deployment_service",
                finding=finding,
                supports=supports,
                confidence=confidence,
                metadata=metadata,
            )
        ]