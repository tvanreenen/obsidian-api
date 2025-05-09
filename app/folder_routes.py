import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_folder,
    validate_new_folder,
    validate_destination_path
)
from app.utils import walk_folders, read_folder_to_response
from app.models import FolderMoveRequest, FolderResponse

obsidian_security = ObsidianHTTPBearer()
folder_router = APIRouter(
    prefix="/folders",
    tags=["folders"],
    dependencies=[Depends(obsidian_security)]
)

@folder_router.get(
    "/", 
    summary="List all folders",
    response_description='List all of the folders in your vault.',
    response_model=list[FolderResponse]
)
def list_folders() -> list[FolderResponse]:
    try:
        return walk_folders()
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault path does not exist")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vault path is not readable")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error accessing vault: {str(e)}")

@folder_router.get(
    "/{vault_folder_path:path}", 
    summary="List files in a folder",
    response_description='List all of the markdown files in the specified folder.',
    response_model=FolderResponse
)
async def list_folder_files(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_existing_folder)]
) -> FolderResponse:
    return read_folder_to_response(vault_folder_path)

@folder_router.post(
    "/{vault_folder_path:path}", 
    summary="Create a new folder",
    response_description='Create a new folder at the specified path.',
    response_model=FolderResponse
)
async def create_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_new_folder)]
) -> FolderResponse:
    try:
        os.makedirs(full_folder_path)
        return read_folder_to_response(vault_folder_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating folder: {str(e)}")

@folder_router.patch(
    "/{vault_folder_path:path}", 
    summary="Move or rename a folder",
    response_description='Move or rename the specified folder to the new specified path.'
)
async def move_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_existing_folder)],
    request_model: FolderMoveRequest
) -> FolderResponse:
    try:
        full_destination_path = validate_destination_path(request_model.new_path, vault_folder_path)
        parent_dir = os.path.dirname(full_destination_path)
        os.makedirs(parent_dir, exist_ok=True)
        os.rename(full_folder_path, full_destination_path)
        return read_folder_to_response(request_model.new_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error moving folder: {str(e)}") 