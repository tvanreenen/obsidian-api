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
from app.models import FileCreateRequest, FilePutRequest, FilePatchRequest, FileResponse

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
    return walk_files()

@file_router.get(
    "/{vault_file_path:path}", 
    summary="Read a file",
    response_description='Get the contents of the markdown file at the specified path.',
    response_model=FileResponse
)
async def read_file(
    vault_file_path: str,
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
    with open(full_file_path, 'w', encoding='utf-8') as f:
        f.write(request_model.content)
    return read_file_to_response(full_file_path)

@file_router.patch(
    "/{vault_file_path:path}",
    summary="Update file content and/or path",
    response_description='Update the file content and/or move/rename the file to a new path.',
    response_model=FileResponse
)
async def patch_file(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: FilePatchRequest = None
) -> FileResponse:
    # If no request model or no fields are provided, return current state
    if not request_model or not request_model.model_dump(exclude_unset=True):
        return read_file_to_response(full_file_path)
        
    # Handle path update if provided
    if request_model.path is not None:
        full_destination_path = validate_destination_path(request_model.path, vault_file_path)
        if os.path.exists(full_destination_path):
            raise HTTPException(status_code=400, detail="Destination file already exists")
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        os.rename(full_file_path, full_destination_path)
        full_file_path = full_destination_path
        vault_file_path = request_model.path

    # Handle content update if provided
    if request_model.content is not None:
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(request_model.content)
    
    # Return the updated file info
    return read_file_to_response(full_file_path)

@file_router.put(
    "/{vault_file_path:path}", 
    summary="Update an existing file",
    response_description='Update the contents of the specified markdown file with the new specified content.',
    response_model=FileResponse
)
async def put_file(
    vault_file_path: str,
    request_model: FilePutRequest,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> FileResponse:
    with open(full_file_path, 'w', encoding='utf-8') as f:
        f.write(request_model.content)
        
    return read_file_to_response(full_file_path)