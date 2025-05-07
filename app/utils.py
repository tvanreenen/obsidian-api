import os
from fastapi import HTTPException
from pathlib import Path

def get_vault_path() -> str:
    path = os.getenv("OBSIDIAN_API_VAULT_PATH")
    if not path:
        raise HTTPException(status_code=400, detail="OBSIDIAN_API_VAULT_PATH environment variable must be set")
    return path

def is_hidden_directory(path: str) -> bool:
    path_parts = Path(path).parts
    current_path = Path(get_vault_path())
    
    for part in path_parts:
        current_path = current_path / part
        if part.startswith('.') and current_path.is_dir():
            return True
            
    return False

def walk_vault(filter_func):
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