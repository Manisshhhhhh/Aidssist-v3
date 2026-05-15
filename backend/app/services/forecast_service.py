from __future__ import annotations

from datetime import datetime, timezone
import math
import re
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from pandas.errors import ParserError

from app.models.forecast_models import (
    ForecastMetrics,
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    HistoricalPoint,
)
from app.repositories.forecast_repository import create_forecast_record
from app.services import artifact_service
from app.services import storage_service


MIN_FORECAST_POINTS = 5


class DatasetNotFoundError(Exception):
    """Raised when a requested dataset cannot be found."""


class ForecastReadError(Exception):
    """Raised when the stored CSV cannot be read."""


class ForecastValidationError(Exception):
    """Raised when the requested forecast cannot be generated."""


def forecast_dataset(dataset_id: str, request: ForecastRequest) -> ForecastResponse:
    metadata = storage_service.load_metadata(dataset_id)
    if metadata is None:
        raise DatasetNotFoundError(f"Dataset '{dataset_id}' was not found.")

    dataframe = load_dataset_frame(dataset_id)
    prepared = prepare_time_series(
        dataframe=dataframe,
        date_column=request.date_column,
        target_column=request.target_column,
    )

    series_frame = prepared.frame
    if len(series_frame) < MIN_FORECAST_POINTS:
        raise ForecastValidationError("At least 5 valid time points are required for forecasting.")

    frequency, frequency_warning = resolve_frequency(series_frame["date"], request.frequency)
    model_used = resolve_model(request.model, len(series_frame))

    assumptions = [
        "Forecast assumes the historical trend continues.",
        "External events and seasonality are not modeled.",
    ]
    warnings = build_initial_warnings(
        series_frame=series_frame,
        requested_periods=request.periods,
        dropped_rows=prepared.dropped_rows,
        duplicate_dates_aggregated=prepared.duplicate_dates_aggregated,
        frequency_warning=frequency_warning,
    )

    if prepared.duplicate_dates_aggregated:
        assumptions.append("Rows sharing the same date were aggregated using the mean target value.")

    forecast_values, fitted_values, residual_std = fit_and_forecast(
        series_frame["value"].to_numpy(dtype=float),
        request.periods,
        model_used,
    )
    metrics = calculate_metrics(series_frame["value"].to_numpy(dtype=float), model_used)
    if metrics.mae is None:
        warnings.append("Backtest metrics require at least 10 historical points and are not available.")

    warnings.extend(volatility_warnings(series_frame["value"].to_numpy(dtype=float), request.periods))

    future_dates = generate_future_dates(series_frame["date"].iloc[-1], frequency, request.periods)
    non_negative_history = bool((series_frame["value"] >= 0).all())
    forecast_points, clamped_lower_bounds = build_forecast_points(
        future_dates=future_dates,
        forecast_values=forecast_values,
        residual_std=residual_std,
        clamp_lower_bound=non_negative_history,
    )
    if clamped_lower_bounds:
        warnings.append("Lower confidence bounds were clamped to 0 because historical values are non-negative.")
        assumptions.append("Forecast lower bounds are constrained to non-negative values for this target.")

    response = ForecastResponse(
        dataset_id=dataset_id,
        date_column=request.date_column,
        target_column=request.target_column,
        model_used=model_used,
        frequency=frequency,
        periods=request.periods,
        historical_points=build_historical_points(series_frame),
        forecast_points=forecast_points,
        metrics=metrics,
        assumptions=dedupe_messages(assumptions),
        warnings=dedupe_messages(warnings),
        created_at=datetime.now(timezone.utc),
    )

    forecast_path = save_forecast_response(response)
    create_forecast_record(response, forecast_path)
    artifact_service.record_path_artifact(
        artifact_type="forecast_json",
        storage_key=storage_service.get_forecast_key(response.dataset_id, forecast_path.name),
        filename=forecast_path.name,
        dataset_id=response.dataset_id,
        content_type="application/json",
        metadata={"date_column": response.date_column, "target_column": response.target_column},
    )
    return response


class PreparedSeries:
    def __init__(self, frame: pd.DataFrame, dropped_rows: int, duplicate_dates_aggregated: bool) -> None:
        self.frame = frame
        self.dropped_rows = dropped_rows
        self.duplicate_dates_aggregated = duplicate_dates_aggregated


def load_dataset_frame(dataset_id: str) -> pd.DataFrame:
    original_path = storage_service.get_original_file_path(dataset_id)
    if not original_path.is_file():
        raise ForecastReadError("Original CSV file is missing.")

    try:
        return pd.read_csv(original_path)
    except (ParserError, UnicodeDecodeError, ValueError) as exc:
        raise ForecastReadError("Stored CSV file could not be read.") from exc


def prepare_time_series(dataframe: pd.DataFrame, date_column: str, target_column: str) -> PreparedSeries:
    if date_column not in dataframe.columns:
        raise ForecastValidationError(f"Date column '{date_column}' was not found.")
    if target_column not in dataframe.columns:
        raise ForecastValidationError(f"Target column '{target_column}' was not found.")

    raw_count = len(dataframe)
    parsed_dates = parse_datetime_series(dataframe[date_column])
    date_non_null_count = int(dataframe[date_column].notna().sum())
    parsed_date_count = int(parsed_dates.notna().sum())
    if date_non_null_count == 0 or parsed_date_count / max(date_non_null_count, 1) < 0.8:
        raise ForecastValidationError(f"Date column '{date_column}' is not parseable as datetime.")

    numeric_target = pd.to_numeric(dataframe[target_column], errors="coerce")
    target_non_null_count = int(dataframe[target_column].notna().sum())
    numeric_target_count = int(numeric_target.notna().sum())
    if target_non_null_count == 0 or numeric_target_count / max(target_non_null_count, 1) < 0.8:
        raise ForecastValidationError(f"Target column '{target_column}' is not numeric.")

    series_frame = pd.DataFrame({"date": parsed_dates, "value": numeric_target}).dropna()
    dropped_rows = raw_count - len(series_frame)
    series_frame = series_frame.sort_values("date")

    row_count_before_aggregation = len(series_frame)
    series_frame = series_frame.groupby("date", as_index=False)["value"].mean()
    duplicate_dates_aggregated = len(series_frame) < row_count_before_aggregation

    return PreparedSeries(
        frame=series_frame.sort_values("date").reset_index(drop=True),
        dropped_rows=dropped_rows,
        duplicate_dates_aggregated=duplicate_dates_aggregated,
    )


def parse_datetime_series(series: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.to_datetime(series, errors="coerce")


def resolve_frequency(dates: pd.Series, requested_frequency: str) -> tuple[str, Optional[str]]:
    if requested_frequency != "auto":
        return requested_frequency, None

    inferred = pd.infer_freq(dates)
    if inferred:
        normalized = normalize_frequency(inferred)
        if normalized:
            return normalized, None

    deltas = dates.sort_values().diff().dropna()
    if deltas.empty:
        raise ForecastValidationError("Could not infer forecast frequency from date values.")

    median_days = deltas.dt.total_seconds().median() / 86400
    if not math.isfinite(median_days) or median_days <= 0:
        raise ForecastValidationError("Could not infer forecast frequency from date values.")

    if median_days <= 2:
        return "D", "Frequency was inferred from the median date gap and may be unreliable."
    if median_days <= 10:
        return "W", "Frequency was inferred from the median date gap and may be unreliable."
    return "M", "Frequency was inferred from the median date gap and may be unreliable."


def normalize_frequency(inferred_frequency: str) -> Optional[str]:
    upper = inferred_frequency.upper()
    if upper.startswith("D"):
        return "D"
    if upper.startswith("W"):
        return "W"
    if upper.startswith("M"):
        return "M"
    return None


def resolve_model(requested_model: str, point_count: int) -> str:
    if requested_model != "auto":
        return requested_model
    if point_count >= 10:
        return "linear_regression"
    return "moving_average"


def fit_and_forecast(values: np.ndarray, periods: int, model_used: str) -> tuple[np.ndarray, np.ndarray, float]:
    if model_used == "linear_regression":
        return linear_regression_forecast(values, periods)
    if model_used == "moving_average":
        return moving_average_forecast(values, periods)
    raise ForecastValidationError(f"Unsupported forecast model '{model_used}'.")


def linear_regression_forecast(values: np.ndarray, periods: int) -> tuple[np.ndarray, np.ndarray, float]:
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    fitted_values = slope * x + intercept
    future_x = np.arange(len(values), len(values) + periods, dtype=float)
    forecast_values = slope * future_x + intercept
    residual_std = safe_std(values - fitted_values)
    return forecast_values, fitted_values, residual_std


def moving_average_forecast(values: np.ndarray, periods: int) -> tuple[np.ndarray, np.ndarray, float]:
    window = min(7, max(3, len(values) // 4))
    recent_average = float(np.mean(values[-window:]))
    fitted_values = np.array(
        [float(np.mean(values[max(0, index - window) : index])) if index > 0 else recent_average for index in range(len(values))]
    )
    residual_std = safe_std(values - fitted_values)
    forecast_values = np.full(periods, recent_average, dtype=float)
    return forecast_values, fitted_values, residual_std


def calculate_metrics(values: np.ndarray, model_used: str) -> ForecastMetrics:
    if len(values) < 10:
        return ForecastMetrics()

    split_index = max(1, int(len(values) * 0.8))
    if len(values) - split_index < 1:
        return ForecastMetrics()

    train_values = values[:split_index]
    validation_values = values[split_index:]
    predictions, _, _ = fit_and_forecast(train_values, len(validation_values), model_used)
    errors = validation_values - predictions
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))

    positive_mask = validation_values > 0
    mape = None
    if positive_mask.any():
        mape = float(np.mean(np.abs(errors[positive_mask] / validation_values[positive_mask])) * 100)

    return ForecastMetrics(
        mae=json_safe_float(mae),
        rmse=json_safe_float(rmse),
        mape=json_safe_float(mape),
    )


def generate_future_dates(last_date: pd.Timestamp, frequency: str, periods: int) -> list[pd.Timestamp]:
    dates: list[pd.Timestamp] = []
    current = pd.Timestamp(last_date)
    for _ in range(periods):
        if frequency == "D":
            current = current + pd.Timedelta(days=1)
        elif frequency == "W":
            current = current + pd.Timedelta(weeks=1)
        elif frequency == "M":
            current = current + pd.DateOffset(months=1)
        else:
            raise ForecastValidationError(f"Unsupported frequency '{frequency}'.")
        dates.append(pd.Timestamp(current))
    return dates


def build_historical_points(series_frame: pd.DataFrame) -> list[HistoricalPoint]:
    return [
        HistoricalPoint(date=pd.Timestamp(row.date).isoformat(), value=float(row.value))
        for row in series_frame.itertuples(index=False)
    ]


def build_forecast_points(
    future_dates: list[pd.Timestamp],
    forecast_values: np.ndarray,
    residual_std: float,
    clamp_lower_bound: bool,
) -> tuple[list[ForecastPoint], bool]:
    points: list[ForecastPoint] = []
    clamped = False

    for date, prediction in zip(future_dates, forecast_values):
        lower_bound = float(prediction - 1.96 * residual_std)
        upper_bound = float(prediction + 1.96 * residual_std)
        if clamp_lower_bound and lower_bound < 0:
            lower_bound = 0.0
            clamped = True

        points.append(
            ForecastPoint(
                date=date.isoformat(),
                predicted_value=json_safe_float(prediction) or 0.0,
                lower_bound=json_safe_float(lower_bound),
                upper_bound=json_safe_float(upper_bound),
            )
        )

    return points, clamped


def build_initial_warnings(
    series_frame: pd.DataFrame,
    requested_periods: int,
    dropped_rows: int,
    duplicate_dates_aggregated: bool,
    frequency_warning: Optional[str],
) -> list[str]:
    warnings: list[str] = []
    point_count = len(series_frame)
    values = series_frame["value"].to_numpy(dtype=float)

    if point_count < 30:
        warnings.append("Dataset has fewer than 30 time points; forecast confidence is limited.")
    if dropped_rows > 0:
        warnings.append(f"{dropped_rows} rows were dropped because date or target values were missing or invalid.")
    if duplicate_dates_aggregated:
        warnings.append("Duplicate dates were aggregated using the mean target value.")
    if frequency_warning:
        warnings.append(frequency_warning)
    if requested_periods > max(point_count // 2, 1):
        warnings.append("Forecast horizon is long relative to the available history.")
    if np.any(values <= 0):
        warnings.append("Non-positive historical values make MAPE less reliable.")

    return warnings


def volatility_warnings(values: np.ndarray, requested_periods: int) -> list[str]:
    warnings: list[str] = []
    mean_value = float(np.mean(values))
    std_value = safe_std(values)
    if mean_value != 0 and abs(std_value / mean_value) > 0.5:
        warnings.append("Target values have high volatility; forecast confidence is limited.")
    if requested_periods > len(values):
        warnings.append("Forecast horizon exceeds the historical series length.")
    return warnings


def save_forecast_response(response: ForecastResponse) -> Path:
    filename = f"forecast_{sanitize_component(response.date_column)}_{sanitize_component(response.target_column)}.json"
    stored = storage_service.get_provider().save_text(
        storage_service.get_forecast_key(response.dataset_id, filename),
        response.model_dump_json(indent=2),
        "application/json",
    )
    local_path = storage_service.get_provider().get_local_path(stored.key)
    if local_path is None:
        raise ForecastReadError("Forecast storage path is unavailable.")
    return local_path


def sanitize_component(value: str) -> str:
    safe_value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return safe_value or "column"


def safe_std(values: np.ndarray) -> float:
    if len(values) <= 1:
        return 0.0
    std_value = float(np.std(values, ddof=1))
    if not math.isfinite(std_value):
        return 0.0
    return std_value


def json_safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    float_value = float(value)
    if math.isnan(float_value) or math.isinf(float_value):
        return None
    return round(float_value, 6)


def dedupe_messages(messages: list[str]) -> list[str]:
    return list(dict.fromkeys(messages))
