from fastapi import FastAPI, Request, HTTPException
from .routes import router as file_router
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title="Obsidian API",
    version="0.1.0",
    description="A FastAPI service for managing and searching an Obsidian vault."
)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return HTTPException(
        status_code=422,
        detail={"errors": exc.errors()}
    )

app.include_router(file_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)