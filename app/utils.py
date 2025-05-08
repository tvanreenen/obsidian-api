import os
from fastapi import HTTPException, status
from pathlib import Path
from datetime import datetime
from app.models import FileResponse, ResourceType, FolderResponse

def get_vault_path() -> str:
    path = os.getenv("OBSIDIAN_API_VAULT_PATH")
    if not path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OBSIDIAN_API_VAULT_PATH environment variable must be set")
    return path

def is_hidden_directory(path: str) -> bool:
    path_parts = Path(path).parts
    current_path = Path(get_vault_path())
    
    for part in path_parts:
        current_path = current_path / part
        if part.startswith('.') and current_path.is_dir():
            return True
            
    return False

def walk_vault(filter_func) -> list[str]:
    vault_path = get_vault_path()
    
    if not os.path.exists(vault_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vault path does not exist: {vault_path}")
    
    if not os.access(vault_path, os.R_OK):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Vault path is not readable: {vault_path}")
    
    items = []
    try:
        for root, dirs, files in os.walk(vault_path):
            dirs[:] = [d for d in dirs if not is_hidden_directory(os.path.join(root, d))]
            files[:] = [f for f in files if not is_hidden_directory(os.path.join(root, f))]
            
            for item in filter_func(root, dirs, files):
                vault_relative_path = os.path.relpath(os.path.join(root, item), vault_path)
                items.append(vault_relative_path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error accessing vault: {str(e)}")
    
    return items

def read_file_to_response(full_file_path: str) -> FileResponse:
    with open(full_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stats = os.stat(full_file_path)
    
    return FileResponse(
        name=os.path.basename(full_file_path),
        path=full_file_path,
        type=ResourceType.FILE,
        size=stats.st_size,
        content=content,
        created=datetime.fromtimestamp(stats.st_ctime),
        modified=datetime.fromtimestamp(stats.st_mtime)
    )

def read_folder_to_response(full_folder_path: str) -> FolderResponse:
    stats = os.stat(full_folder_path)
    children = []
    
    for root, _, filenames in os.walk(full_folder_path):
        for filename in filenames:
            if filename.endswith('.md'):
                full_file_path = os.path.join(root, filename)
                children.append(read_file_to_response(full_file_path))
    
    return FolderResponse(
        name=os.path.basename(full_folder_path),
        path=os.path.relpath(full_folder_path, get_vault_path()),
        type=ResourceType.FOLDER,
        size=stats.st_size,
        created=datetime.fromtimestamp(stats.st_ctime),
        modified=datetime.fromtimestamp(stats.st_mtime),
        children=children
    )
