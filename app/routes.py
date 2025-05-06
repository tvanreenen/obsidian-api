import os
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from .models import FileContentBody, NewPathBody
from .validation import (
    validate_existing_markdown_file,
    validate_new_markdown_file,
    validate_existing_folder,
    validate_new_folder,
    validate_destination_path,
    get_vault_path,
    is_hidden_directory
)
from .auth import verify_token

router = APIRouter()

def _walk_vault(filter_func):
    vault_path = get_vault_path()
    
    if not os.path.exists(vault_path):
        raise HTTPException(status_code=400, detail=f"Vault path does not exist: {vault_path}")
    
    if not os.access(vault_path, os.R_OK):
        raise HTTPException(status_code=400, detail=f"Vault path is not readable: {vault_path}")
    
    items = []
    try:
        for root, dirs, files in os.walk(vault_path):
            dirs[:] = [d for d in dirs if not is_hidden_directory(os.path.join(root, d))]
            files[:] = [f for f in files if not is_hidden_directory(os.path.join(root, f))]
            
            for item in filter_func(root, dirs, files):
                vault_relative_path = os.path.relpath(os.path.join(root, item), vault_path)
                items.append(vault_relative_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error accessing vault: {str(e)}")
    
    return items

# Files endpoints
@router.get("/files", summary="List markdown files", dependencies=[Depends(verify_token)])
def list_files():
    return _walk_vault(lambda root, dirs, files: [file for file in files if file.endswith(".md")])

@router.get("/files/{vault_file_path:path}", summary="Read a specific file", dependencies=[Depends(verify_token)])
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

@router.post("/files/{vault_file_path:path}", summary="Create a new file", dependencies=[Depends(verify_token)])
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

@router.patch("/files/{vault_file_path:path}", summary="Move/Rename a file")
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

@router.put("/files/{vault_file_path:path}", summary="Update an existing file", dependencies=[Depends(verify_token)])
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

# Folders endpoints
@router.get("/folders", summary="List all folders", dependencies=[Depends(verify_token)])
def list_folders():
    return _walk_vault(lambda root, dirs, files: dirs)

@router.get("/folders/{vault_folder_path:path}", summary="List files in a specific folder", dependencies=[Depends(verify_token)])
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
        raise HTTPException(status_code=500, detail=f"Error listing folder contents: {str(e)}")

@router.post("/folders/{vault_folder_path:path}", summary="Create a new folder", dependencies=[Depends(verify_token)])
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
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")

@router.patch("/folders/{vault_folder_path:path}", summary="Move/Rename a folder", dependencies=[Depends(verify_token)])
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
        raise HTTPException(status_code=500, detail=f"Error moving folder: {str(e)}")