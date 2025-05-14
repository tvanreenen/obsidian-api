# Standard library imports
import os
# Third-party imports
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from typing import Annotated
# Local application imports
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_markdown_file,
    validate_new_markdown_file,
    validate_destination_path,
    validate_utf8_content
)
from app.utils import (
    # Read operations
    read_file,
    read_markdown_file,
    read_stats,
    walk_files,
    get_markdown_file_model,
    # Write operations
    write_content,
    write_body,
    write_frontmatter,
    merge_frontmatter,
    write_markdown_file,
)
from app.models import (
    MarkdownFile,
    FileMetadata,
    MetadataPatchRequest,
    MarkdownContent
)

# Router setup
obsidian_security = ObsidianHTTPBearer()
file_router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(obsidian_security)]
)

# List operations
@file_router.get(
    "/", 
    summary="List Files", 
    description="List all markdown files in your vault with their metadata, including path, size, and modification dates."
)
async def list_files() -> list[MarkdownFile]:
    return await walk_files()

# Read operations
@file_router.get(
    "/{vault_file_path:path}/raw", 
    summary="Get Raw File",
    response_description='Get the raw contents of the markdown file at the specified path, including frontmatter and body content exactly as stored.',
    response_class=PlainTextResponse
)
async def read_raw_file(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> str:
    return await read_file(full_file_path)

@file_router.get(
    "/{vault_file_path:path}/metadata", 
    summary="Get File Metadata",
    response_description='Get the file\'s metadata including name, path, size, creation date, and last modification date.'
)
async def read_file_metadata(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> FileMetadata:
    return await read_stats(full_file_path)

@file_router.get(
    "/{vault_file_path:path}/frontmatter", 
    summary="Get File Frontmatter",
    response_description='Get the YAML frontmatter of the file as a JSON object.'
)
async def read_file_frontmatter(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> dict:
    _, frontmatter = await read_markdown_file(full_file_path)
    return frontmatter or {}

@file_router.get(
    "/{vault_file_path:path}/body", 
    summary="Get File Body",
    response_description='Get the markdown body content of the file, excluding the frontmatter section.',
    response_class=PlainTextResponse
)
async def read_file_body(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> str:
    body, _ = await read_markdown_file(full_file_path)
    return body

@file_router.get(
    "/{vault_file_path:path}", 
    summary="Get File",
    response_description='Get the complete file representation including metadata, YAML frontmatter, and markdown body content.'
)
async def read_file_structured(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> MarkdownFile:
    return await get_markdown_file_model(full_file_path)

# Create operations

@file_router.post(
    "/{vault_file_path:path}/raw", 
    summary="Create File (Raw)",
    response_description='Create a new markdown file at the specified path with raw text content. The content should include YAML frontmatter (between --- markers) followed by markdown body content.'
)
async def create_file_raw(
    request: Request,
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_new_markdown_file)],
    content: Annotated[str, Depends(validate_utf8_content)]
) -> MarkdownFile:
    await write_content(full_file_path, content)
    return await get_markdown_file_model(full_file_path)

@file_router.post(
    "/{vault_file_path:path}", 
    summary="Create File (Structured)",
    response_description='Create a new markdown file at the specified path using a JSON object with \'frontmatter\' (YAML object) and \'body\' (markdown string) fields.'
)
async def create_file_structured(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_new_markdown_file)],
    request_model: MarkdownContent
) -> MarkdownFile:
    await write_markdown_file(full_file_path, request_model.frontmatter, request_model.body)
    return await get_markdown_file_model(full_file_path)


# Update operations
@file_router.put(
    "/{vault_file_path:path}/raw",
    summary="Replace Raw Content",
    response_description='Replace the entire raw content of the file. The content should include YAML frontmatter (between --- markers) followed by markdown body content.'
)
async def put_raw_file(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request: Request,
    content: Annotated[str, Depends(validate_utf8_content)]
) -> MarkdownFile:
    await write_content(full_file_path, content)
    return await get_markdown_file_model(full_file_path)

@file_router.put(
    "/{vault_file_path:path}/frontmatter",
    summary="Replace Frontmatter",
    response_description='Replace the entire YAML frontmatter of the file with a new JSON object containing frontmatter data.'
)
async def put_file_frontmatter(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    json_body: dict
) -> MarkdownFile:
    await write_frontmatter(full_file_path, json_body)
    return await get_markdown_file_model(full_file_path)

@file_router.put(
    "/{vault_file_path:path}/body",
    summary="Replace Body",
    response_description='Replace the entire markdown body content of the file, preserving the frontmatter.'
)
async def put_file_body(
    request: Request,
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    content: Annotated[str, Depends(validate_utf8_content)]
) -> MarkdownFile:
    await write_body(full_file_path, content)
    return await get_markdown_file_model(full_file_path)

@file_router.patch(
    "/{vault_file_path:path}/metadata",
    summary="Merge File Metadata",
    response_description='Merge new metadata with existing file metadata, including moving/renaming the file to a new path within the vault.'
)
async def patch_file_metadata(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: MetadataPatchRequest
) -> MarkdownFile:
    if request_model.path is not None:
        full_destination_path = validate_destination_path(request_model.path, vault_file_path)
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        os.rename(full_file_path, full_destination_path)
    
    return await get_markdown_file_model(full_destination_path)

@file_router.patch(
    "/{vault_file_path:path}/frontmatter",
    summary="Merge Frontmatter",
    response_description='Merge a new JSON object containing frontmatter data with the existing YAML frontmatter.'
)
async def patch_file_frontmatter(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    json_body: dict
) -> MarkdownFile:
    await merge_frontmatter(full_file_path, json_body)
    return await get_markdown_file_model(full_file_path)