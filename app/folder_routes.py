import os
from fastapi import APIRouter, Depends
from typing import Annotated
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_folder,
    validate_new_folder,
    validate_destination_path
)
from app.utils import walk_folders, get_folder_response
from app.models import FolderResponse, FolderPatchRequest

obsidian_security = ObsidianHTTPBearer()
folder_router = APIRouter(
    prefix="/folders",
    tags=["folders"],
    dependencies=[Depends(obsidian_security)]
)

@folder_router.get(
    "/", 
    summary="List Folders",
    description="List all folders in your vault.",
    response_model=list[FolderResponse]
)
async def list_folders() -> list[FolderResponse]:
    return walk_folders()

@folder_router.get(
    "/{vault_folder_path:path}", 
    summary="Get Folder",
    response_description='Get the folder at the specified path.',
    response_model=FolderResponse
)
async def list_folder_files(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_existing_folder)]
) -> FolderResponse:
    return get_folder_response(full_folder_path)

@folder_router.post(
    "/{vault_folder_path:path}", 
    summary="Create Folder",
    response_description='Create a new folder at the specified path.',
    response_model=FolderResponse
)
async def create_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_new_folder)]
) -> FolderResponse:
    os.makedirs(full_folder_path, exist_ok=True)
    return get_folder_response(full_folder_path)

@folder_router.patch(
    "/{vault_folder_path:path}",
    summary="Update Folder",
    response_description='Move or rename the specified folder to the new specified path.',
    response_model=FolderResponse
)
async def patch_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_existing_folder)],
    request_model: FolderPatchRequest = None
) -> FolderResponse:
    # If no request model or no fields are provided, return current state
    if not request_model or not request_model.model_dump(exclude_unset=True):
        return get_folder_response(full_folder_path)
        
    # Handle path update if provided
    if request_model.path is not None:
        full_destination_path = validate_destination_path(request_model.path, vault_folder_path)
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        os.rename(full_folder_path, full_destination_path)
    return get_folder_response(full_destination_path)