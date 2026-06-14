from pprint import pprint

from app.services.json_data_service import JsonDataService


def main() -> None:
    data_service = JsonDataService()

    alert = data_service.get_alert("ALERT-001")
    print("\nAlert:")
    pprint(alert)

    if not alert:
        raise ValueError("ALERT-001 not found")

    model_id = alert["model_id"]

    print("\nModel Metrics:")
    pprint(data_service.get_model_metrics(model_id))

    print("\nFeature Drift:")
    pprint(data_service.get_feature_drift(model_id))

    print("\nPrediction Samples:")
    pprint(data_service.get_prediction_samples(model_id))

    print("\nDeployments:")
    pprint(data_service.get_deployments(model_id))

    print("\nSchema Profile:")
    pprint(data_service.get_schema_profile(model_id))

    print("\nData Quality:")
    pprint(data_service.get_data_quality(model_id))


if __name__ == "__main__":
    main()