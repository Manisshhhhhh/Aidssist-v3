from typing import Optional

from fastapi import APIRouter, Depends

from app.core.errors import not_found
from app.core.permissions import require_dataset_role
from app.core.security import require_api_key
from app.core.config import get_settings
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.dataset_models import DatasetDeleteResponse, DatasetMetadata
from app.repositories.workspace_repository import list_workspaces_for_user
from app.services.workspace_service import can_access_workspace
from app.services.dataset_service import delete_dataset, get_dataset, list_datasets


router = APIRouter(tags=["datasets"], dependencies=[Depends(require_api_key)])


@router.get("/datasets", response_model=list[DatasetMetadata])
def get_datasets(
    workspace_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> list[DatasetMetadata]:
    if get_settings().user_auth_enabled and current_user:
        if workspace_id is not None:
            if not can_access_workspace(workspace_id, current_user, "viewer"):
                return []
            return list_datasets(workspace_id=workspace_id, include_ownerless=False)
        workspace_ids = [workspace.id for workspace in list_workspaces_for_user(current_user)]
        return list_datasets(workspace_ids=workspace_ids, include_ownerless=False)
    return list_datasets(workspace_id=workspace_id)


@router.get("/datasets/{dataset_id}", response_model=DatasetMetadata)
def get_dataset_detail(
    dataset_id: str,
    _: Optional[User] = Depends(require_dataset_role("viewer")),
) -> DatasetMetadata:
    metadata = get_dataset(dataset_id)
    if metadata is None:
        raise not_found(f"Dataset '{dataset_id}' was not found.")
    return metadata


@router.delete("/datasets/{dataset_id}", response_model=DatasetDeleteResponse)
def delete_dataset_route(
    dataset_id: str,
    _: Optional[User] = Depends(require_dataset_role("editor")),
) -> DatasetDeleteResponse:
    deleted = delete_dataset(dataset_id)
    if not deleted:
        raise not_found(f"Dataset '{dataset_id}' was not found.")

    return DatasetDeleteResponse(
        dataset_id=dataset_id,
        deleted=True,
        message="Dataset deleted successfully.",
    )
