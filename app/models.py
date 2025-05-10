from pydantic import BaseModel, Field
from typing import Optional, List, Literal
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

class FilePutRequest(BaseModel):
    content: str = Field(..., description="Content to replace the existing file with")

class FilePatchRequest(BaseModel):
    path: Optional[str] = Field(None, description="New path to move or rename the file to")
    content: Optional[str] = Field(None, description="New content to update the file with")

class FolderPatchRequest(BaseModel):
    path: Optional[str] = Field(None, description="New path to move or rename the folder to")

# response
    
class FileResponse(ResourceMetadata):
    type: Literal[ResourceType.FILE] = Field(..., description="The type of the entry: 'file'")
    size: int = Field(..., description="Size of the file in bytes")
    content: Optional[str] = Field(None, description="The full content of the file")

class FolderResponse(ResourceMetadata):
    type: Literal[ResourceType.FOLDER] = Field(..., description="The type of the entry: 'folder'")
    children: Optional[List[FileResponse]] = Field(None, description="List of child markdown files")