# Obsidian API

An API for managing markdown files and folders in your Obsidian vault.

Built with:
- FastAPI for the web framework
- Pydantic for data validation
- Uvicorn for the ASGI server
- Pytest for testing
- UV for package management

> ⚠️ **Warning**: This is an experimental API for personal use on a local network. It is not secured and should not be exposed to the internet or used in production environments.

## Setup

Set your Obsidian vault path:
```bash
export OBSIDIAN_API_VAULT_PATH="/path/to/your/obsidian/vault"
```

## Running

Start the server:
```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## API Endpoints

### Files
- `GET /files` - List all markdown files
- `GET /files/{path}` - Read the contents of a specific file
- `POST /files/{path}` - Create a new file
- `PATCH /files/{path}` - Move/Rename a file
- `PUT /files{path}` - Update the contents of an existing file

### Folders
- `GET /folders` - List all folders
- `GET /folders/{path}` - List files in a specific folder
- `POST /folders/{path}` - Create a new folder
- `PATCH /folders/{path}` - Move/Rename a folder

For detailed API documentation, including request/response schemas and examples, visit the Swagger UI at `http://localhost:8000/docs`.

## Testing

Run tests (a few different styles for reference):
```bash
uv run pytest 
uv run pytest tests/test_routes.py
uv run pytest tests/test_routes.py::test_move_file
```
Use the  `-v` flag to provide more detailed output.

## Reason for Creating

While useful in itself, this API is part of a larger personal experiment in building a personal AI agent that integrates my Obsidian knowledge base as a tool. While Obsidian Copilot is a great plugin, I wanted the ability to integrate my knowledge base into other platforms like n8n, Claude desktop, etc.

Future Plans:
- Make deployable in a local Docker services.
- Provide and authentication mechanism.
- Implement a MCP server for the API.
- Add additional endpoints like DELETE and perhaps MERGE. But I'd want configuration or authorization to be in plact to control access.
- Provide file/folder metadata. Perhaps integrating file frontmatter into metadata.

