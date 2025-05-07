from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastmcp import FastMCP
from app.file_routes import file_router
from app.folder_routes import folder_router
from app.path_validation import validation_exception_handler

app = FastAPI(
    title="Obsidian API",
    version="0.2.0",
    description="A personal RESTful API for managing markdown files and folders in your Obsidian vault."
)

app.include_router(file_router)
app.include_router(folder_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
