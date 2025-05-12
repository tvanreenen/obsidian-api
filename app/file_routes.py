import os
from fastapi import APIRouter, Depends, Response
from typing import Annotated
from app.authentication import ObsidianHTTPBearer
from app.path_validation import (
    validate_existing_markdown_file,
    validate_new_markdown_file,
    validate_destination_path
)
from app.utils import (
    walk_files, 
    get_file_response,
    get_file_metadata_response,
    get_file_frontmatter_response,
    get_file_body_response,
    get_raw_response
)
from app.models import (
    FileCreateRequest, 
    ParsedFileResponse,
    BaseFileResponse,
    FrontmatterResponse,
    BodyResponse,
    MetadataPatchRequest,
    FrontmatterPutRequest,
    FrontmatterPatchRequest,
    BodyPutRequest,
    RawPutRequest
)

obsidian_security = ObsidianHTTPBearer()
file_router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(obsidian_security)]
)

@file_router.get(
    "/", 
    summary="List Files", 
    description="List all markdown files in your vault.",
    response_model=list[ParsedFileResponse]
)
def list_files():
    return walk_files()

@file_router.get(
    "/{vault_file_path:path}/raw", 
    summary="Get Raw File",
    response_description='Get the raw contents of the markdown file at the specified path, including frontmatter.',
    response_class=Response
)
async def read_raw_file(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> Response:
    return get_raw_response(full_file_path)

@file_router.get(
    "/{vault_file_path:path}/metadata", 
    summary="Get File Metadata",
    response_description='Get just the metadata of the file (name, path, size, dates).',
    response_model=BaseFileResponse
)
async def read_file_metadata(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> BaseFileResponse:
    return get_file_metadata_response(full_file_path)

@file_router.get(
    "/{vault_file_path:path}/frontmatter", 
    summary="Get File Frontmatter",
    response_description='Get just the frontmatter of the file.',
    response_model=FrontmatterResponse
)
async def read_file_frontmatter(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> FrontmatterResponse:
    return get_file_frontmatter_response(full_file_path)

@file_router.get(
    "/{vault_file_path:path}/body", 
    summary="Get File Body",
    response_description='Get just the body content of the file without frontmatter.',
    response_model=BodyResponse
)
async def read_file_body(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> BodyResponse:
    return get_file_body_response(full_file_path)

@file_router.get(
    "/{vault_file_path:path}", 
    summary="Get File",
    response_description='Get the complete file including metadata, frontmatter, and body.',
    response_model=ParsedFileResponse
)
async def read_file(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)]
) -> ParsedFileResponse:
    return get_file_response(full_file_path)

@file_router.post(
    "/{vault_file_path:path}", 
    summary="Create File",
    response_description='Create a new markdown file at the specified path with the specified content.',
    response_model=ParsedFileResponse
)
async def create_file(
    vault_file_path: str,
    request_model: FileCreateRequest,
    full_file_path: Annotated[str, Depends(validate_new_markdown_file)]
) -> ParsedFileResponse:
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
    with open(full_file_path, 'w', encoding='utf-8') as f:
        f.write(request_model.content)
    return get_file_response(full_file_path)

@file_router.patch(
    "/{vault_file_path:path}/metadata",
    summary="Update File Metadata",
    response_description='Update the file metadata (move/rename).',
    response_model=BaseFileResponse
)
async def patch_file_metadata(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: MetadataPatchRequest
) -> BaseFileResponse:
    if request_model.path is not None:
        full_destination_path = validate_destination_path(request_model.path, vault_file_path)
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        os.rename(full_file_path, full_destination_path)
        full_file_path = full_destination_path
    
    return get_file_metadata_response(full_file_path)

@file_router.put(
    "/{vault_file_path:path}/frontmatter",
    summary="Replace Frontmatter",
    response_description='Replace the entire frontmatter of the file.',
    response_model=FrontmatterResponse
)
async def put_file_frontmatter(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: FrontmatterPutRequest
) -> FrontmatterResponse:
    update_frontmatter(full_file_path, request_model.frontmatter)
    return get_file_frontmatter_response(full_file_path)

@file_router.patch(
    "/{vault_file_path:path}/frontmatter",
    summary="Update Frontmatter",
    response_description='Update the frontmatter of the file by merging with existing frontmatter.',
    response_model=FrontmatterResponse
)
async def patch_file_frontmatter(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: FrontmatterPatchRequest
) -> FrontmatterResponse:
    merge_frontmatter(full_file_path, request_model.frontmatter)
    return get_file_frontmatter_response(full_file_path)

@file_router.put(
    "/{vault_file_path:path}/body",
    summary="Replace Body",
    response_description='Replace the entire body content of the file.',
    response_model=BodyResponse
)
async def put_file_body(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: BodyPutRequest
) -> BodyResponse:
    update_body(full_file_path, request_model.body)
    return get_file_body_response(full_file_path)

@file_router.put(
    "/{vault_file_path:path}/raw",
    summary="Replace Raw Content",
    response_description='Replace the entire raw content of the file.',
    response_class=Response
)
async def put_raw_file(
    vault_file_path: str,
    full_file_path: Annotated[str, Depends(validate_existing_markdown_file)],
    request_model: RawPutRequest
) -> Response:
    update_file_content(full_file_path, request_model.content)
    return get_raw_response(full_file_path)