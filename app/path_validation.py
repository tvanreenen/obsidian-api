import os
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from typing import Optional
from app.utils import get_vault_path, is_hidden

def _get_full_path(vault_relative_path: str) -> str:
    return os.path.join(get_vault_path(), vault_relative_path)

def _validate_path(
    vault_relative_path: str,
    must_exist: bool = True,
    must_be_markdown: bool = False
) -> str:
    full_path = _get_full_path(vault_relative_path)

    if not os.path.abspath(full_path).startswith(os.path.abspath(get_vault_path())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
    
    if is_hidden(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Path not found: {vault_relative_path}")
    
    path_exists = os.path.exists(full_path)
    
    if must_exist and not path_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Path not found: {vault_relative_path}")
    elif not must_exist and path_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Path already exists: {vault_relative_path}")
    
    if must_be_markdown and not full_path.endswith('.md'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File must have .md extension: {vault_relative_path}")
    
    return full_path

def validate_existing_markdown_file(vault_file_path: str) -> str:
    full_path = _validate_path(vault_file_path, must_exist=True, must_be_markdown=True)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a file: {vault_file_path}")
    return full_path

def validate_existing_folder(vault_folder_path: str) -> str:
    full_path = _validate_path(vault_folder_path, must_exist=True)
    if not os.path.isdir(full_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a folder: {vault_folder_path}")
    return full_path

def validate_new_markdown_file(vault_file_path: str) -> str:
    return _validate_path(vault_file_path, must_exist=False, must_be_markdown=True)

def validate_new_folder(vault_folder_path: str) -> str:
    return _validate_path(vault_folder_path, must_exist=False)

def validate_destination_path(vault_destination_path: str, vault_source_path: Optional[str] = None) -> str:
    return _validate_path(vault_destination_path, must_exist=False)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"errors": exc.errors()})

async def validate_utf8_content(request: Request) -> str:
    content = await request.body()
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content must be UTF-8 encoded text")