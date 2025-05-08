import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_markdown_file,
    validate_new_markdown_file,
    validate_destination_path
)
from app.utils import walk_files, read_file_to_response
from app.models import FileCreateRequest, FileUpdateRequest, FileMoveRequest, FileResponse

obsidian_security = ObsidianHTTPBearer()
file_router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(obsidian_security)]
)

@file_router.get(
    "/", 
    summary="List files", 
    description="List all markdown files in your vault.",
    response_model=list[FileResponse]
)
def list_files():
    try:
        return walk_files()
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault path does not exist")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vault path is not readable")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error accessing vault: {str(e)}")

@file_router.get(
    "/{vault_file_path:path}", 
    summary="Read a file",
    response_description='Get the contents of the markdown file at the specified path.',
    response_model=FileResponse
)
async def read_file(
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> FileResponse:
    return read_file_to_response(full_file_path)

@file_router.post(
    "/{vault_file_path:path}", 
    summary="Create a new file",
    response_description='Create a new markdown file at the specified path with the specified content.',
    response_model=FileResponse
)
async def create_file(
    vault_file_path: str,
    request_model: FileCreateRequest,
    full_file_path: Annotated[str, Depends(validate_new_markdown_file)]
) -> FileResponse:
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
    
    try:
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(request_model.content)
        return read_file_to_response(full_file_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating file: {str(e)}")

@file_router.patch(
    "/{vault_file_path:path}",
    summary="Move or rename a file",
    response_description='Move or rename the specified markdown file to the new specified path.',
    response_model=FileResponse
)
async def move_file(
    vault_file_path: str,
    request_model: FileMoveRequest,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> FileResponse:
    try:
        full_destination_path = validate_destination_path(request_model.new_path, vault_file_path)
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        os.rename(full_file_path, full_destination_path)
        return read_file_to_response(full_destination_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error moving file: {str(e)}")

@file_router.put(
    "/{vault_file_path:path}", 
    summary="Update an existing file",
    response_description='Update the contents of the specified markdown file with the new specified content.',
    response_model=FileResponse
)
async def update_file(
    request_model: FileUpdateRequest,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> FileResponse:
    try:
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(request_model.content)
        return read_file_to_response(full_file_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating file: {str(e)}") 