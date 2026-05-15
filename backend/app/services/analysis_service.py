from __future__ import annotations

import json

import pandas as pd
from pandas.errors import ParserError

from app.models.analysis_models import AnalysisResult
from app.repositories.analysis_repository import upsert_analysis
from app.services import artifact_service
from app.services import storage_service
from app.services.chart_service import recommend_charts
from app.services.insight_service import generate_insights
from app.services.profiling_service import profile_dataset


class DatasetNotFoundError(Exception):
    """Raised when a requested dataset cannot be found."""


class AnalysisReadError(Exception):
    """Raised when the stored CSV cannot be read for analysis."""


def analyze_dataset(dataset_id: str) -> AnalysisResult:
    metadata = storage_service.load_metadata(dataset_id)
    if metadata is None:
        raise DatasetNotFoundError(f"Dataset '{dataset_id}' was not found.")

    original_path = storage_service.get_original_file_path(dataset_id)
    if not original_path.is_file():
        raise AnalysisReadError("Original CSV file is missing.")

    try:
        dataframe = pd.read_csv(original_path)
    except (ParserError, UnicodeDecodeError, ValueError) as exc:
        raise AnalysisReadError("Stored CSV file could not be read.") from exc

    if dataframe.columns.empty:
        raise AnalysisReadError("Stored CSV file does not contain columns.")

    analysis = profile_dataset(dataset_id, dataframe)
    analysis.insights = generate_insights(
        dataframe=dataframe,
        columns=analysis.columns,
        quality=analysis.quality,
        correlations=analysis.correlations,
    )
    analysis.recommended_charts = recommend_charts(analysis)
    analysis_path = storage_service.save_analysis(analysis)
    upsert_analysis(analysis, analysis_path)
    artifact_service.record_path_artifact(
        artifact_type="analysis_json",
        storage_key=storage_service.get_analysis_key(dataset_id),
        filename=storage_service.ANALYSIS_FILENAME,
        dataset_id=dataset_id,
        content_type="application/json",
    )
    return analysis


def load_analysis(dataset_id: str) -> AnalysisResult | None:
    analysis_path = storage_service.get_analysis_path(dataset_id)
    if not analysis_path.is_file():
        return None

    with analysis_path.open("r", encoding="utf-8") as analysis_file:
        payload = json.load(analysis_file)
    return AnalysisResult.model_validate(payload)
