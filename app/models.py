from pydantic import BaseModel, Field

class FileContentBody(BaseModel):
    content: str = Field(..., description="Content of the file to create or update")

class NewPathBody(BaseModel):
    new_path: str = Field(..., min_length=1, description="New path for the file or folder") 