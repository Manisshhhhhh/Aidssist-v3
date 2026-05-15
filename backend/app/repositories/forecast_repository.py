from __future__ import annotations

from pathlib import Path

from app.db.models import ForecastRecord
from app.db.session import new_session
from app.models.forecast_models import ForecastResponse


def create_forecast_record(response: ForecastResponse, forecast_path: Path) -> ForecastRecord:
    session = new_session()
    try:
        record = ForecastRecord(
            dataset_id=response.dataset_id,
            date_column=response.date_column,
            target_column=response.target_column,
            model_used=response.model_used,
            frequency=response.frequency,
            periods=response.periods,
            forecast_path=str(forecast_path),
            created_at=response.created_at,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def latest_forecast_record(dataset_id: str) -> ForecastRecord | None:
    session = new_session()
    try:
        return (
            session.query(ForecastRecord)
            .filter(ForecastRecord.dataset_id == dataset_id)
            .order_by(ForecastRecord.created_at.desc(), ForecastRecord.id.desc())
            .first()
        )
    finally:
        session.close()
