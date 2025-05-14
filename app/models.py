from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import StrEnum
from datetime import datetime

class ResourceType(StrEnum):
    FILE = "file"
    FOLDER = "folder"

class ResourceMetadata(BaseModel):
    name: str = Field(..., description="The name of the file or folder")
    path: str = Field(..., description="The full relative path from the vault root")
    created: Optional[datetime] = Field(None, description="The timestamp when the file or folder was created")
    modified: Optional[datetime] = Field(None, description="The timestamp when the file or folder was last modified")
 
class FileMetadata(ResourceMetadata):
    type: Literal[ResourceType.FILE] = Field(..., description="The type of the entry: 'file'")
    size: int = Field(..., description="Size of the file in bytes")
    created: datetime = Field(..., description="When the file was created")
    modified: datetime = Field(..., description="When the file was last modified")

class FolderMetadata(ResourceMetadata):
    type: Literal[ResourceType.FOLDER] = Field(..., description="The type of the entry: 'folder'")

class MarkdownContent(BaseModel):
    frontmatter: Optional[dict] = Field(None, description="The YAML frontmatter of the file")
    body: Optional[str] = Field(None, description="The body content of the file without frontmatter")

class MarkdownFile(BaseModel):
    metadata: FileMetadata = Field(..., description="The metadata of the markdown file")
    content: MarkdownContent = Field(..., description="The content of the markdown file including frontmatter and body")

class Folder(BaseModel):
    metadata: FolderMetadata = Field(..., description="The metadata of the folder")

class MetadataPatchRequest(BaseModel):
    path: Optional[str] = Field(None, description="New path to move or rename the file to")
