import os
from fastapi import HTTPException, status
from pathlib import Path
from datetime import datetime
from app.models import FileResponse, ResourceType, FolderResponse
from typing import Literal

def get_vault_path() -> str:
    path = os.getenv("OBSIDIAN_API_VAULT_PATH")
    if not path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OBSIDIAN_API_VAULT_PATH environment variable must be set")
    return path

def is_hidden(path: str) -> bool:
    path_parts = Path(path).parts
    current_path = Path(get_vault_path())
    
    for part in path_parts:
        current_path = current_path / part
        if part.startswith('.') and current_path.is_dir():
            return True
            
    return False

def walk_files() -> list[FileResponse]:
    vault_path = get_vault_path()
    items = []
    
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                full_file_path = os.path.join(root, file)
                if not is_hidden(full_file_path):
                    items.append(read_file_to_response(full_file_path, "absolute"))
    
    return items

def walk_folders() -> list[FolderResponse]:
    vault_path = get_vault_path()
    items = []
    
    for root, dirs, _ in os.walk(vault_path):
        for dir_name in dirs:
            full_dir_path = os.path.join(root, dir_name)
            if not is_hidden(full_dir_path):
                items.append(read_folder_to_response(full_dir_path, "absolute", include_children=False))
    
    return items

def read_file_to_response(path: str, path_type: Literal["absolute", "relative"] = "relative") -> FileResponse:
    if path_type == "relative":
        full_file_path = os.path.join(get_vault_path(), path)
    else:
        full_file_path = path
        path = os.path.relpath(path, get_vault_path())
        
    with open(full_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stats = os.stat(full_file_path)
    
    return FileResponse(
        name=os.path.basename(path),
        path=path,
        type=ResourceType.FILE,
        size=stats.st_size,
        content=content,
        created=datetime.fromtimestamp(stats.st_ctime),
        modified=datetime.fromtimestamp(stats.st_mtime)
    )

def read_folder_to_response(path: str, path_type: Literal["absolute", "relative"] = "relative", include_children: bool = True) -> FolderResponse:
    if path_type == "relative":
        full_folder_path = os.path.join(get_vault_path(), path)
    else:
        full_folder_path = path
        path = os.path.relpath(path, get_vault_path())
        
    stats = os.stat(full_folder_path)
    children = []
    
    if include_children:
        for root, _, filenames in os.walk(full_folder_path):
            for filename in sorted(filenames):
                if filename.endswith('.md'):
                    full_file_path = os.path.join(root, filename)
                    children.append(read_file_to_response(full_file_path, "absolute"))
        children.sort(key=lambda x: x.path)
    
    return FolderResponse(
        name=os.path.basename(path),
        path=path,
        type=ResourceType.FOLDER,
        size=stats.st_size,
        created=datetime.fromtimestamp(stats.st_ctime),
        modified=datetime.fromtimestamp(stats.st_mtime),
        children=children if include_children else None
    )
