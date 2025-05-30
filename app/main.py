from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastmcp import FastMCP
from app.file_routes import file_router
from app.folder_routes import folder_router
from app.path_validation import validation_exception_handler

app = FastAPI(
    title="Obsidian API",
    version="0.4.0",
    description="A personal RESTful API for managing markdown files and folders in your Obsidian vault."
)

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )

@app.exception_handler(PermissionError)
async def permission_error_handler(request, exc):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied"
    )

@app.exception_handler(FileExistsError)
async def file_exists_error_handler(request, exc):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Resource already exists"
    )

app.include_router(file_router)
app.include_router(folder_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

if __name__ == "__main__":
    mcp = FastMCP.from_fastapi(app=app, exclude={
        "put_raw_file",
        "put_file_frontmatter",
        "put_file_body"
    })
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
