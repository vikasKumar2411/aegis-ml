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

    def _filter_rows(
        self,
        rows: List[Dict[str, Any]],
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filtered = [
            row for row in rows
            if row.get("model_id") == model_id
        ]

        if alert_id is not None:
            alert_scoped_rows = [
                row for row in filtered
                if row.get("alert_id") == alert_id
            ]

            if alert_scoped_rows:
                filtered = alert_scoped_rows

        if model_version is not None:
            version_scoped_rows = [
                row for row in filtered
                if row.get("model_version") == model_version
            ]

            if version_scoped_rows:
                filtered = version_scoped_rows

        return filtered


    def get_model_metrics(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_json("model_metrics.json")
        return self._filter_rows(
            rows=rows,
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )


    def get_feature_drift(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_json("feature_drift_results.json")
        return self._filter_rows(
            rows=rows,
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )


    def get_prediction_samples(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_json("prediction_samples.json")
        return self._filter_rows(
            rows=rows,
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )


    def get_deployments(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_json("deployment_events.json")
        return self._filter_rows(
            rows=rows,
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )


    def get_schema_profile(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        rows = self._load_json("schema_profiles.json")
        filtered = self._filter_rows(
            rows=rows,
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )
        return filtered[0] if filtered else None


    def get_data_quality(
        self,
        model_id: str,
        alert_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._load_json("data_quality_results.json")
        return self._filter_rows(
            rows=rows,
            model_id=model_id,
            alert_id=alert_id,
            model_version=model_version,
        )