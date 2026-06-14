import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class JsonDataService:
    """
    Lightweight JSON-backed data access layer for AegisML MVP.

    In production, this will later be replaced by Postgres / warehouse /
    monitoring system connectors. For MVP, this keeps the diagnostic tools
    simple and testable.
    """

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)

    def _load_json(self, filename: str) -> List[Dict[str, Any]]:
        path = self.data_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"Required data file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(f"Expected list JSON in {path}, got {type(data).__name__}")

        return data

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        alerts = self._load_json("alerts.json")
        return next((alert for alert in alerts if alert.get("alert_id") == alert_id), None)

    def get_model_metrics(self, model_id: str) -> List[Dict[str, Any]]:
        rows = self._load_json("model_metrics.json")
        return [row for row in rows if row.get("model_id") == model_id]

    def get_feature_drift(self, model_id: str) -> List[Dict[str, Any]]:
        rows = self._load_json("feature_drift_results.json")
        return [row for row in rows if row.get("model_id") == model_id]

    def get_prediction_samples(self, model_id: str) -> List[Dict[str, Any]]:
        rows = self._load_json("prediction_samples.json")
        return [row for row in rows if row.get("model_id") == model_id]

    def get_deployments(self, model_id: str) -> List[Dict[str, Any]]:
        rows = self._load_json("deployment_events.json")
        return [row for row in rows if row.get("model_id") == model_id]

    def get_schema_profile(self, model_id: str) -> Optional[Dict[str, Any]]:
        rows = self._load_json("schema_profiles.json")
        return next((row for row in rows if row.get("model_id") == model_id), None)

    def get_data_quality(self, model_id: str) -> List[Dict[str, Any]]:
        rows = self._load_json("data_quality_results.json")
        return [row for row in rows if row.get("model_id") == model_id]