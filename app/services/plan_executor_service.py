from typing import Callable, Dict, List

from app.services.data_quality_service import DataQualityService
from app.services.deployment_service import DeploymentService
from app.services.feature_drift_service import FeatureDriftService
from app.services.json_data_service import JsonDataService
from app.services.model_performance_service import ModelPerformanceService
from app.services.prediction_error_service import PredictionErrorService
from app.services.schema_drift_service import SchemaDriftService
from app.state.pipeline_state import DiagnosticStep, EvidenceItem, PipelineState


class PlanExecutorService:
    """
    Executes approved diagnostic steps by invoking deterministic diagnostic tools.
    """

    def __init__(self, data_service: JsonDataService) -> None:
        self.data_service = data_service

        self.model_performance_service = ModelPerformanceService(data_service)
        self.feature_drift_service = FeatureDriftService(data_service)
        self.prediction_error_service = PredictionErrorService(data_service)
        self.deployment_service = DeploymentService(data_service)
        self.schema_drift_service = SchemaDriftService(data_service)
        self.data_quality_service = DataQualityService(data_service)

    def execute(
        self,
        state: PipelineState,
        approved_steps: List[DiagnosticStep],
    ) -> PipelineState:
        for step in approved_steps:
            try:
                evidence_items = self._execute_step(state, step)

                for item in evidence_items:
                    state.add_evidence(item)

                state.mark_step_completed(step.action)

            except Exception as exc:
                state.add_error(
                    f"Step {step.step_id} failed: {step.action}. Error: {exc}"
                )

        return state

    def _execute_step(
        self,
        state: PipelineState,
        step: DiagnosticStep,
    ) -> List[EvidenceItem]:
        model_id = state.model_id

        if step.action == "check_model_performance":
            alert_metric = state.alert.get("metric", "")
            return self.model_performance_service.run(
                model_id=model_id,
                alert_metric=alert_metric,
                alert_id=state.alert_id,
                model_version=state.alert.get("model_version"),
            )
            

        if step.action == "check_feature_drift":
            return self.feature_drift_service.run(
                model_id=model_id,
                alert_id=state.alert_id,
                model_version=state.alert.get("model_version"),
            )

        if step.action == "analyze_prediction_errors":
            return self.prediction_error_service.run(
                model_id=model_id,
                alert_id=state.alert_id,
                model_version=state.alert.get("model_version"),
            )

        if step.action == "check_recent_deployments":
            return self.deployment_service.run(
                model_id=model_id,
                alert_id=state.alert_id,
                model_version=state.alert.get("model_version"),
            )

        if step.action == "check_schema_drift":
            return self.schema_drift_service.run(
                model_id=model_id,
                alert_id=state.alert_id,
                model_version=state.alert.get("model_version"),
            )

        if step.action == "check_data_quality":
            return self.data_quality_service.run(
                model_id=model_id,
                alert_id=state.alert_id,
                model_version=state.alert.get("model_version"),
            )

        raise ValueError(f"Unsupported diagnostic action: {step.action}")