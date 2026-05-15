from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.diagnostics import ensure_admin_or_local
from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.preflight_models import PreflightResponse
from app.core.preflight import run_preflight


router = APIRouter(prefix="/diagnostics", tags=["diagnostics"], dependencies=[Depends(require_api_key)])


@router.get("/preflight", response_model=PreflightResponse)
def preflight_diagnostics(current_user: Optional[User] = Depends(get_current_user_required)) -> PreflightResponse:
    ensure_admin_or_local(current_user)
    return run_preflight()
