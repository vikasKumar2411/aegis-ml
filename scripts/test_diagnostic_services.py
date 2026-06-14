from pprint import pprint

from app.services.data_quality_service import DataQualityService
from app.services.deployment_service import DeploymentService
from app.services.feature_drift_service import FeatureDriftService
from app.services.json_data_service import JsonDataService
from app.services.model_performance_service import ModelPerformanceService
from app.services.prediction_error_service import PredictionErrorService
from app.services.schema_drift_service import SchemaDriftService


def main() -> None:
    data_service = JsonDataService()

    alert = data_service.get_alert("ALERT-001")
    if not alert:
        raise ValueError("ALERT-001 not found")

    model_id = alert["model_id"]
    metric = alert["metric"]

    services = [
        ("Model Performance", ModelPerformanceService(data_service).run(model_id, metric)),
        ("Feature Drift", FeatureDriftService(data_service).run(model_id)),
        ("Prediction Errors", PredictionErrorService(data_service).run(model_id)),
        ("Deployments", DeploymentService(data_service).run(model_id)),
        ("Schema Drift", SchemaDriftService(data_service).run(model_id)),
        ("Data Quality", DataQualityService(data_service).run(model_id)),
    ]

    for name, evidence_items in services:
        print(f"\n{name}:")
        for item in evidence_items:
            pprint(item.model_dump())


if __name__ == "__main__":
    main()