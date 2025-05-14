# Standard library imports
import os

# Third-party imports
from fastapi import APIRouter, Depends
from typing import Annotated

# Local application imports
from app.authentication import ObsidianHTTPBearer
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
    Path
)

# Router setup
obsidian_security = ObsidianHTTPBearer()
folder_router = APIRouter(
    prefix="/folders",
    tags=["folders"],
    dependencies=[Depends(obsidian_security)]
)

# List operations
@folder_router.get(
    "/", 
    summary="List Folders",
    description="List all folders in your vault."
)
async def list_folders() -> list[Folder]:
    return await walk_folders()

# Read operations
@folder_router.get(
    "/{vault_folder_path:path}", 
    summary="Get Folder",
    response_description='Get the folder\'s metadata including name, path, size, creation date, and last modification date.'
)
async def read_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_existing_folder)]
) -> Folder:
    return await get_folder_model(full_folder_path)

# Create operations
@folder_router.post(
    "/{vault_folder_path:path}", 
    summary="Create Folder",
    response_description='Create a new folder at the specified path.'
)
async def create_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_new_folder)]
) -> Folder:
    os.makedirs(full_folder_path, exist_ok=True)
    return await get_folder_model(full_folder_path)

# Update operations
@folder_router.patch(
    "/{vault_folder_path:path}",
    summary="Move Folder",
    response_description='Move/rename the folder to a new path within the vault.'
)
async def move_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_existing_folder)],
    request_model: Path
) -> Folder:
    full_destination_path = validate_destination_path(request_model.path, vault_folder_path)
    os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
    os.rename(full_folder_path, full_destination_path)
    return await get_folder_model(full_destination_path)