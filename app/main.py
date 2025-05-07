from fastapi import FastAPI, Request, HTTPException
from app.file_routes import file_router
from app.folder_routes import folder_router
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title="Obsidian API",
    version="0.2.0",
    description="A FastAPI service for managing and searching an Obsidian vault."
)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return HTTPException(
        status_code=422,
        detail={"errors": exc.errors()}
    )

app.include_router(file_router)
app.include_router(folder_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
