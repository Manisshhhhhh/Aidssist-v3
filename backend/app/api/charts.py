from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.errors import not_found
from app.core.permissions import require_dataset_role
from app.core.security import require_api_key
from app.models.chart_models import ChartDataResponse
from app.services.chart_data_service import (
    AnalysisRequiredError,
    ChartDataError,
    ChartNotFoundError,
    DatasetNotFoundError,
    get_chart_data,
)


router = APIRouter(tags=["charts"], dependencies=[Depends(require_api_key)])


@router.get("/datasets/{dataset_id}/charts/{chart_id}/data", response_model=ChartDataResponse)
def get_chart_data_route(
    dataset_id: str,
    chart_id: str,
    time_range: Optional[str] = Query(default=None),
    _: object = Depends(require_dataset_role("viewer")),
) -> ChartDataResponse:
    try:
        return get_chart_data(dataset_id, chart_id, time_range=time_range)
    except (DatasetNotFoundError, ChartNotFoundError) as exc:
        raise not_found(str(exc)) from exc
    except (AnalysisRequiredError, ChartDataError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
