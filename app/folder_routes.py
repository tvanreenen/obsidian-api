import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_folder,
    validate_new_folder,
    validate_destination_path
)
from app.utils import walk_vault, read_folder_to_response
from app.models import NewPathBody, FolderResponse

obsidian_security = ObsidianHTTPBearer()
folder_router = APIRouter(
    prefix="/folders",
    tags=["folders"],
    dependencies=[Depends(obsidian_security)]
)

@folder_router.get(
    "/", 
    summary="List all folders",
    response_description='List all of the folders in your vault.'
)
def list_folders():
    return walk_vault(lambda root, dirs, files: dirs)

@folder_router.get(
    "/{vault_folder_path:path}", 
    summary="List files in a folder",
    response_description='List all of the markdown files in the specified folder.',
    response_model=FolderResponse
)
async def list_folder_files(
    full_folder_path: Annotated[str, Depends(validate_existing_folder)]
):
    return read_folder_to_response(full_folder_path)

@folder_router.post(
    "/{vault_folder_path:path}", 
    summary="Create a new folder",
    response_description='Create a new folder at the specified path.',
    response_model=FolderResponse
)
async def create_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_new_folder)]
):
    try:
        os.makedirs(full_folder_path)
        return read_folder_to_response(full_folder_path)
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
    move_path: NewPathBody
):
    try:
        full_path = validate_existing_folder(vault_folder_path)
        full_destination_path = validate_destination_path(move_path.new_path, vault_folder_path)
        
        parent_dir = os.path.dirname(full_destination_path)
        os.makedirs(parent_dir, exist_ok=True)
        
        os.rename(full_path, full_destination_path)
        return {"message": f"Folder moved successfully to {move_path.new_path}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error moving folder: {str(e)}") 