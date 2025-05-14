import os
import anyio
from pathlib import Path
from datetime import datetime
import frontmatter
from typing import Optional
from app.models import ResourceType, Folder, MarkdownFile, FileMetadata, MarkdownContent, FolderMetadata

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

# Read Operations

async def read_file(full_file_path: str) -> str:
    async with await anyio.open_file(full_file_path, 'r', encoding='utf-8') as f:
        return await f.read()

async def read_markdown_file(full_file_path: str) -> tuple[str, Optional[dict]]:
    content = await read_file(full_file_path)
    post = frontmatter.loads(content)
    return post.content, post.metadata if post.metadata else None

async def read_stats(full_path: str) -> dict:
    path = os.path.relpath(full_path, get_vault_path())
    stats = os.stat(full_path)
    
    return {
        "name": os.path.basename(path),
        "path": path,
        "type": ResourceType.FILE if os.path.isfile(full_path) else ResourceType.FOLDER,
        "size": stats.st_size,
        "created": datetime.fromtimestamp(stats.st_ctime),
        "modified": datetime.fromtimestamp(stats.st_mtime)
    }

# Write Operations

async def write_content(full_file_path: str, content: str) -> None:
    async with await anyio.open_file(full_file_path, 'w', encoding='utf-8') as f:
        await f.write(content)

async def write_frontmatter(full_file_path: str, frontmatter_data: dict) -> None:
    content = await read_file(full_file_path)
    post = frontmatter.loads(content)
    post.metadata = frontmatter_data
    await write_content(full_file_path, frontmatter.dumps(post))

async def merge_frontmatter(full_file_path: str, frontmatter_data: dict) -> None:
    content = await read_file(full_file_path)
    post = frontmatter.loads(content)
    current_metadata = post.metadata or {}
    post.metadata = {**current_metadata, **frontmatter_data}
    await write_content(full_file_path, frontmatter.dumps(post))

async def write_body(full_file_path: str, body: str) -> None:
    content = await read_file(full_file_path)
    post = frontmatter.loads(content)
    post.content = body
    await write_content(full_file_path, frontmatter.dumps(post))

async def write_markdown_file(full_file_path: str, file_frontmatter: Optional[dict] = {}, file_body: Optional[str] = None) -> None:
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

    post = frontmatter.Post(
        content=file_body or "",
        **file_frontmatter if file_frontmatter else {}
    )
    dumped = frontmatter.dumps(post)
    await write_content(full_file_path, dumped)

# Response Generators

async def get_markdown_file_model(full_file_path: str) -> MarkdownFile:
    stats = await read_stats(full_file_path)
    body, frontmatter_data = await read_markdown_file(full_file_path)
    return MarkdownFile(
        metadata=FileMetadata(**stats),
        content=MarkdownContent(
            body=body,
            frontmatter=frontmatter_data
        )
    )

async def get_folder_model(full_folder_path: str) -> Folder:
    stats = await read_stats(full_folder_path)
    return Folder(
        metadata=FolderMetadata(**stats)
    )

# Walk Helpers

async def walk_folders() -> list[Folder]:
    vault_path = get_vault_path()
    items = []
    
    for root, dirs, _ in os.walk(vault_path):
        for dir_name in dirs:
            full_dir_path = os.path.join(root, dir_name)
            if not is_hidden(full_dir_path):
                items.append(await get_folder_model(full_dir_path))
    
    return items

async def walk_files() -> list[MarkdownFile]:
    vault_path = get_vault_path()
    items = []
    
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                full_file_path = os.path.join(root, file)
                if not is_hidden(full_file_path):
                    items.append(await get_markdown_file_model(full_file_path))
    
    return items
