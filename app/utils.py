import os
from fastapi import Response
from pathlib import Path
from datetime import datetime
import frontmatter
from typing import Optional
from app.models import ResourceType, FolderResponse, ParsedFileResponse, BaseFileResponse, FrontmatterResponse, BodyResponse

# Core Utilities

def get_vault_path() -> str:
    path = os.getenv("OBSIDIAN_API_VAULT_PATH")
    return path

def is_hidden(path: str) -> bool:
    path_parts = Path(path).parts
    current_path = Path(get_vault_path())
    
    for part in path_parts:
        current_path = current_path / part
        if part.startswith('.') and current_path.is_dir():
            return True
            
    return False

# Component Generators

def get_raw_content(full_file_path: str) -> str:
    with open(full_file_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_parsed_content(content: str) -> tuple[str, Optional[dict]]:
    post = frontmatter.loads(content)
    return post.content, post.metadata if post.metadata else None

def get_file_metadata(full_file_path: str) -> dict:
    path = os.path.relpath(full_file_path, get_vault_path())
    stats = os.stat(full_file_path)
    
    return {
        "name": os.path.basename(path),
        "path": path,
        "type": ResourceType.FILE,
        "size": stats.st_size,
        "created": datetime.fromtimestamp(stats.st_ctime),
        "modified": datetime.fromtimestamp(stats.st_mtime)
    }

# Response Generators

def get_raw_response(full_file_path: str) -> Response:
    content = get_raw_content(full_file_path)
    return Response(content=content, media_type="text/plain")

def get_file_response(full_file_path: str) -> ParsedFileResponse:
    metadata = get_file_metadata(full_file_path)
    content = get_raw_content(full_file_path)
    body, frontmatter_data = get_parsed_content(content)
    return ParsedFileResponse(
        **metadata,
        body=body,
        frontmatter=frontmatter_data
    )

def get_file_metadata_response(full_file_path: str) -> BaseFileResponse:
    return BaseFileResponse(**get_file_metadata(full_file_path))

def get_file_frontmatter_response(full_file_path: str) -> FrontmatterResponse:
    content = get_raw_content(full_file_path)
    _, frontmatter_data = get_parsed_content(content)
    return FrontmatterResponse(frontmatter=frontmatter_data)

def get_file_body_response(full_file_path: str) -> BodyResponse:
    content = get_raw_content(full_file_path)
    body, _ = get_parsed_content(content)
    return BodyResponse(body=body)

def get_folder_response(full_folder_path: str) -> FolderResponse:
    path = os.path.relpath(full_folder_path, get_vault_path())
    stats = os.stat(full_folder_path)
    
    return FolderResponse(
        name=os.path.basename(path),
        path=path,
        type=ResourceType.FOLDER,
        size=stats.st_size,
        created=datetime.fromtimestamp(stats.st_ctime),
        modified=datetime.fromtimestamp(stats.st_mtime)
    )

def update_file_content(full_file_path: str, content: str) -> None:
    with open(full_file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_frontmatter(full_file_path: str, frontmatter_data: dict) -> None:
    content = get_raw_content(full_file_path)
    post = frontmatter.loads(content)
    post.metadata = frontmatter_data
    update_file_content(full_file_path, frontmatter.dumps(post))

def update_body(full_file_path: str, body: str) -> None:
    content = get_raw_content(full_file_path)
    post = frontmatter.loads(content)
    post.content = body
    update_file_content(full_file_path, frontmatter.dumps(post))

def merge_frontmatter(full_file_path: str, frontmatter_updates: dict) -> None:
    content = get_raw_content(full_file_path)
    post = frontmatter.loads(content)
    current_metadata = post.metadata or {}
    post.metadata = {**current_metadata, **frontmatter_updates}
    update_file_content(full_file_path, frontmatter.dumps(post))

# Walk Helpers

def walk_folders() -> list[FolderResponse]:
    vault_path = get_vault_path()
    items = []
    
    for root, dirs, _ in os.walk(vault_path):
        for dir_name in dirs:
            full_dir_path = os.path.join(root, dir_name)
            if not is_hidden(full_dir_path):
                items.append(get_folder_response(full_dir_path))
    
    return items

def walk_files() -> list[ParsedFileResponse]:
    vault_path = get_vault_path()
    items = []
    
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                full_file_path = os.path.join(root, file)
                if not is_hidden(full_file_path):
                    items.append(get_file_response(full_file_path))
    
    return items
