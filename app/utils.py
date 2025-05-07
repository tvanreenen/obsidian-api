import os
from fastapi import HTTPException
from app.validation import get_vault_path, is_hidden_directory

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