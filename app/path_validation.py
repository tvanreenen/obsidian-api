"""
Path validation dependencies for FastAPI endpoints.

These validators are designed to be injected into FastAPI endpoints using Depends().
They handle validation of vault-relative paths and convert them to full system paths,
ensuring paths are valid, exist (or don't exist) as required, and are within the vault.
"""

import os
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from typing import Optional, Literal
from app.utils import get_vault_path, is_hidden_directory

def _get_full_path(vault_relative_path: str) -> str:
    full_path = os.path.join(get_vault_path(), vault_relative_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(get_vault_path())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
    return full_path

def _validate_path(
    vault_relative_path: str,
    path_type: Literal["file", "folder"],
    must_exist: bool = True,
    must_be_markdown: bool = False
) -> str:
    full_path = _get_full_path(vault_relative_path)
    
    if is_hidden_directory(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{path_type.capitalize()} not found: {vault_relative_path}")
    
    if must_exist:
        if not os.path.exists(full_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{path_type.capitalize()} not found: {vault_relative_path}")
        if path_type == "file" and not os.path.isfile(full_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a file: {vault_relative_path}")
        elif path_type == "folder" and not os.path.isdir(full_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a folder: {vault_relative_path}")
    else:
        if os.path.exists(full_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{path_type.capitalize()} already exists: {vault_relative_path}")
    
    if must_be_markdown and not full_path.endswith('.md'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File must have .md extension: {vault_relative_path}")
    
    return full_path

def validate_existing_markdown_file(vault_file_path: str) -> str:
    return _validate_path(vault_file_path, "file", must_exist=True, must_be_markdown=True)

def validate_existing_folder(vault_folder_path: str) -> str:
    return _validate_path(vault_folder_path, "folder", must_exist=True)

def validate_new_markdown_file(vault_file_path: str) -> str:
    return _validate_path(vault_file_path, "file", must_exist=False, must_be_markdown=True)

def validate_new_folder(vault_folder_path: str) -> str:
    return _validate_path(vault_folder_path, "folder", must_exist=False)

def validate_destination_path(vault_destination_path: str, vault_source_path: Optional[str] = None) -> str:
    full_path = _get_full_path(vault_destination_path)
    if vault_source_path:
        source_full_path = _get_full_path(vault_source_path)
        if os.path.normpath(full_path) == os.path.normpath(source_full_path):
            return full_path
    if os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path already exists: {vault_destination_path}")
    return full_path

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"errors": exc.errors()}) 