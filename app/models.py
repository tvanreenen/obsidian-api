from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from enum import StrEnum
from datetime import datetime

# base

class ResourceType(StrEnum):
    FILE = "file"
    FOLDER = "folder"

class ResourceMetadata(BaseModel):
    name: str = Field(..., description="The name of the file or folder")
    path: str = Field(..., description="The full relative path from the vault root")
    created: Optional[datetime] = Field(None, description="The timestamp when the file or folder was created")
    modified: Optional[datetime] = Field(None, description="The timestamp when the file or folder was last modified")

# request

class FileCreateRequest(BaseModel):
     content: str = Field(..., description="Content to write to the new file")

class MetadataPatchRequest(BaseModel):
    path: Optional[str] = Field(None, description="New path to move or rename the file to")

class FrontmatterPutRequest(BaseModel):
    frontmatter: Dict[str, Any] = Field(..., description="Complete frontmatter to replace existing frontmatter")

class FrontmatterPatchRequest(BaseModel):
    frontmatter: Dict[str, Any] = Field(..., description="Frontmatter updates to merge with existing frontmatter")

class BodyPutRequest(BaseModel):
    body: str = Field(..., description="Complete body content to replace existing body")

class RawPutRequest(BaseModel):
    content: str = Field(..., description="Complete raw content to replace existing content")

class FolderPatchRequest(BaseModel):
    path: Optional[str] = Field(None, description="New path to move or rename the folder to")

# response
    
class BaseFileResponse(ResourceMetadata):
    type: Literal[ResourceType.FILE] = Field(..., description="The type of the entry: 'file'")
    size: int = Field(..., description="Size of the file in bytes")
    created: datetime = Field(..., description="When the file was created")
    modified: datetime = Field(..., description="When the file was last modified")

class FrontmatterResponse(BaseModel):
    frontmatter: Optional[Dict[str, Any]] = Field(None, description="The YAML frontmatter of the file")

class BodyResponse(BaseModel):
    body: str = Field(..., description="The body content of the file without frontmatter")

class ParsedFileResponse(BaseFileResponse, FrontmatterResponse, BodyResponse):
    pass

class FolderResponse(ResourceMetadata):
    type: Literal[ResourceType.FOLDER] = Field(..., description="The type of the entry: 'folder'")
