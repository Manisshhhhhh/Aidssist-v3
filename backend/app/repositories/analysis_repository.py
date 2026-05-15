from __future__ import annotations

from pathlib import Path

from app.db.models import AnalysisRecord
from app.db.session import new_session
from app.models.analysis_models import AnalysisResult


def upsert_analysis(analysis: AnalysisResult, analysis_path: Path) -> AnalysisRecord:
    session = new_session()
    try:
        record = session.query(AnalysisRecord).filter(AnalysisRecord.dataset_id == analysis.dataset_id).one_or_none()
        if record is None:
            record = AnalysisRecord(dataset_id=analysis.dataset_id, created_at=analysis.created_at, analysis_path=str(analysis_path))
            session.add(record)

        record.analysis_path = str(analysis_path)
        record.quality_score = analysis.quality.quality_score
        record.row_count = analysis.row_count
        record.column_count = analysis.column_count
        record.insight_count = len(analysis.insights)
        record.chart_count = len(analysis.recommended_charts)
        record.created_at = analysis.created_at
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()
