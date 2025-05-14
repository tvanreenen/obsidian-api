from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import StrEnum
from datetime import datetime

class ResourceType(StrEnum):
    FILE = "file"
    FOLDER = "folder"

class ResourceMetadata(BaseModel):
    name: str = Field(..., description="Name of the file or folder")
    path: str = Field(..., description="Full relative path from the vault root")
    created: Optional[datetime] = Field(None, description="When the file or folder was created")
    modified: Optional[datetime] = Field(None, description="When the file or folder was last modified")
 
class FileMetadata(ResourceMetadata):
    type: Literal[ResourceType.FILE] = Field(..., description="Literal value indicating this is a file")
    size: int = Field(..., description="Size of the file in bytes")
    created: datetime = Field(..., description="When the file was created")
    modified: datetime = Field(..., description="When the file was last modified")

class FolderMetadata(ResourceMetadata):
    type: Literal[ResourceType.FOLDER] = Field(..., description="Literal value indicating this is a folder")

class MarkdownContent(BaseModel):
    frontmatter: Optional[dict] = Field(None, description="YAML frontmatter of the file")
    body: Optional[str] = Field(None, description="Body content of the file without frontmatter")

class MarkdownFile(BaseModel):
    metadata: FileMetadata = Field(..., description="File metadata including name, path, timestamps, and size")
    content: MarkdownContent = Field(..., description="Content of the markdown file including frontmatter and body")

class Folder(BaseModel):
    metadata: FolderMetadata = Field(..., description="Folder metadata including name, path, and timestamps")

class Path(BaseModel):
    path: Optional[str] = Field(None, description="Target path for moving or renaming a file, relative to the vault root")
