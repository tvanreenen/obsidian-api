import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_markdown_file,
    validate_new_markdown_file,
    validate_destination_path
)
from app.utils import walk_vault, read_file_to_response
from app.models import FileContentBody, NewPathBody, FileResponse

obsidian_security = ObsidianHTTPBearer()
file_router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(obsidian_security)]
)

@file_router.get(
    "/", 
    summary="List files", 
    description="List the file paths to all of the markdown files in your vault."
)
def list_files():
    return walk_vault(lambda root, dirs, files: [file for file in files if file.endswith(".md")])

@file_router.get(
    "/{vault_file_path:path}", 
    summary="Read a file",
    response_description='Get the contents of the markdown file at the specified path.',
    response_model=FileResponse
)
async def read_file(
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
):
    return read_file_to_response(full_file_path)

@file_router.post(
    "/{vault_file_path:path}", 
    summary="Create a new file",
    response_description='Create a new markdown file at the specified path with the specified content.'
)
async def create_file(
    vault_file_path: str,
    file_content: FileContentBody,
    full_file_path: Annotated[str, Depends(validate_new_markdown_file)]
):
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
    
    try:
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(file_content.content)
        return {"message": f"File created successfully: {vault_file_path}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating file: {str(e)}")

@file_router.patch(
    "/{vault_file_path:path}",
    summary="Move or rename a file",
    response_description='Move or rename the specified markdown file to the new specified path.'
)
async def move_file(
    vault_file_path: str,
    move_path: NewPathBody,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
):
    try:
        full_destination_path = validate_destination_path(move_path.new_path, vault_file_path)
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        os.rename(full_file_path, full_destination_path)
        return {"message": f"File moved successfully to {move_path.new_path}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error moving file: {str(e)}")

@file_router.put(
    "/{vault_file_path:path}", 
    summary="Update an existing file",
    response_description='Update the contents of the specified markdown file with the new specified content.'
)
async def update_file(
    vault_file_path: str,
    file_content: FileContentBody,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
):
    try:
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(file_content.content)
        return {"message": f"File updated successfully: {vault_file_path}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating file: {str(e)}") 