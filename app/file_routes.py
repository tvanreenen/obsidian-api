import os
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from app.models import FileContentBody, NewPathBody
from app.validation import (
    validate_existing_markdown_file,
    validate_new_markdown_file,
    validate_destination_path
)
from app.dependencies import ObsidianHTTPBearer
from app.utils import walk_vault

file_router = APIRouter(
    prefix="/files",
    tags=["files"]
)

obsidian_security = ObsidianHTTPBearer()

@file_router.get("/", summary="List markdown files", dependencies=[Depends(obsidian_security)])
def list_files():
    return walk_vault(lambda root, dirs, files: [file for file in files if file.endswith(".md")])

@file_router.get("/{vault_file_path:path}", summary="Read a specific file", dependencies=[Depends(obsidian_security)])
async def read_file(
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
):
    try:
        with open(full_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@file_router.post("/{vault_file_path:path}", summary="Create a new file", dependencies=[Depends(obsidian_security)])
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
        raise HTTPException(status_code=500, detail=f"Error creating file: {str(e)}")

@file_router.patch("/{vault_file_path:path}", summary="Move/Rename a file", dependencies=[Depends(obsidian_security)])
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
        raise HTTPException(status_code=500, detail=f"Error moving file: {str(e)}")

@file_router.put("/{vault_file_path:path}", summary="Update an existing file", dependencies=[Depends(obsidian_security)])
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
        raise HTTPException(status_code=500, detail=f"Error updating file: {str(e)}") 