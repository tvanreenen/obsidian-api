# Standard library imports
import os

# Third-party imports
from fastapi import APIRouter, Depends, Path
from typing import Annotated

# Local application imports
from app.authentication import get_auth_dependency
from app.path_validation import (
    validate_existing_folder,
    validate_new_folder,
    validate_destination_path
)
from app.utils import (
    # Read operations
    walk_folders,
    get_folder_model,
)
from app.models import (
    Folder,
    PathModel
)

# Router setup
folder_router = APIRouter(
    prefix="/folders",
    tags=["folders"],
    dependencies=[Depends(get_auth_dependency())]
)

# List operations
@folder_router.get(
    "/", 
    operation_id="getAllFolders",
    summary="Get All Folders",
    description="List all folders in your vault."
)
async def list_folders() -> list[Folder]:
    return await walk_folders()

# Read operations
@folder_router.get(
    "/{vault_folder_path:path}", 
    operation_id="getFolder",
    summary="Get Folder",
    response_description='Get the folder\'s metadata including name, path, size, creation date, and last modification date.'
)
async def read_folder(
    vault_folder_path: Annotated[str, Path(..., description="The path of the folder to read")],
    full_folder_path: Annotated[str, Depends(validate_existing_folder)]
) -> Folder:
    return await get_folder_model(full_folder_path)

# Create operations
@folder_router.post(
    "/{vault_folder_path:path}", 
    operation_id="createFolder",
    summary="Create Folder",
    response_description='Create a new folder at the specified path.'
)
async def create_folder(
    vault_folder_path: Annotated[str, Path(..., description="The path of the folder to create")],
    full_folder_path: Annotated[str, Depends(validate_new_folder)]
) -> Folder:
    os.makedirs(full_folder_path, exist_ok=True)
    return await get_folder_model(full_folder_path)

# Update operations
@folder_router.patch(
    "/{vault_folder_path:path}",
    operation_id="updateFolder",
    summary="Update Folder",
    response_description='Move or rename the folder to a new path within the vault.'
)
async def move_folder(
    vault_folder_path: Annotated[str, Path(..., description="The path of the folder to move")],
    full_folder_path: Annotated[str, Depends(validate_existing_folder)],
    request_model: PathModel
) -> Folder:
    full_destination_path = validate_destination_path(request_model.path, vault_folder_path)
    os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
    os.rename(full_folder_path, full_destination_path)
    return await get_folder_model(full_destination_path)