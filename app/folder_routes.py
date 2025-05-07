import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.models import NewPathBody
from app.path_validation import (
    validate_existing_folder,
    validate_new_folder,
    validate_destination_path
)
from app.authentication import ObsidianHTTPBearer
from app.utils import walk_vault, get_vault_path

folder_router = APIRouter(
    prefix="/folders",
    tags=["folders"]
)

obsidian_security = ObsidianHTTPBearer()

@folder_router.get("/", summary="List all folders", dependencies=[Depends(obsidian_security)])
def list_folders():
    return walk_vault(lambda root, dirs, files: dirs)

@folder_router.get("/{vault_folder_path:path}", summary="List files in a specific folder", dependencies=[Depends(obsidian_security)])
async def list_folder_files(
    full_folder_path: Annotated[str, Depends(validate_existing_folder)]
):
    try:
        files = []
        for root, _, filenames in os.walk(full_folder_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    vault_relative_path = os.path.relpath(os.path.join(root, filename), get_vault_path())
                    files.append(vault_relative_path)
        return files
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error listing folder contents: {str(e)}")

@folder_router.post("/{vault_folder_path:path}", summary="Create a new folder", dependencies=[Depends(obsidian_security)])
async def create_folder(
    vault_folder_path: str,
    full_folder_path: Annotated[str, Depends(validate_new_folder)]
):
    try:
        os.makedirs(full_folder_path)
        return {"message": f"Folder created successfully: {vault_folder_path}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating folder: {str(e)}")

@folder_router.patch("/{vault_folder_path:path}", summary="Move/Rename a folder", dependencies=[Depends(obsidian_security)])
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