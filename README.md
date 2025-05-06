![Obsidian API](obsidian-api.webp)

# Obsidian API

A personal RESTful API for managing markdown files and folders in your [Obsidian](https://obsidian.md/) vault.

Built with:
- [FastAPI](https://github.com/FastAPI/FastAPI) for the web framework
- [Pydantic](https://github.com/pydantic/pydantic) for data validation
- [Uvicorn](https://github.com/encode/uvicorn) for the ASGI server
- [Pytest](https://github.com/pytest-dev/pytest) for testing
- [UV](https://github.com/astral-sh/uv) for package management
- [Docker](https://www.docker.com/) for containerization

## Setup

Create a `.env` file in the project root with your Obsidian vault path and API key:
```bash
OBSIDIAN_VAULT_PATH="/path/to/your/obsidian/vault"
OBSIDIAN_AUTH_ENABLED="true"  # Set to "true" to enable authentication. Default is "false".
OBSIDIAN_API_KEY="your-secret-api-key"  # Required if authentication is enabled
```

### Local Environment

Start the server:
```bash
source .env
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Docker Environment

Build and start the container:
```bash
docker compose up --build -d
```

The API will be available at:
- `http://localhost:8000` (from your machine)
- `http://<your-ip-address>:8000` (from other devices on your network)
- `http://obsidian-api:8000` (from other containers in the same Docker network)

Note: The container mounts your Obsidian vault as a volume at `/mnt/vault` inside the container.

## Security

### Authentication

The API uses Bearer token authentication. By default, authentication is disabled, and no API key is required. To enable authentication, set the following environment variable:

```bash
OBSIDIAN_AUTH_ENABLED=true
```

Once enabled, all endpoints require a valid API key in the `Authorization` header:

```http
Authorization: Bearer your-secret-api-key
```

Set your API key using the `OBSIDIAN_API_KEY` environment variable. Use a strong, unique key and do not share it publicly.

### HTTPS Support

> ⚠️ **Warning**: This API does not provide HTTPS on its own. Even with bearer authentication enabled, you must use a secure reverse proxy (e.g., NGINX, Traefik, or Cloudflare Tunnel) to provide HTTPS before exposing the server to the public internet. This protects both credentials and sensitive data from interception.

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

I've enjoyed using the [Cursor](https://www.cursor.com/)-like [Obsidian Copilot](https://github.com/logancyang/obsidian-copilot) plugin to interact with my knowledge base, but ultimately, I wanted the flexibility to connect it to a wider range of tools—like [N8N](https://n8n.io/), [Claude Desktop](https://claude.ai/download), and various agent- and RAG-based experiments. Building an API was a natural first step toward that and it sounded like an fun hands-on exercise in its own right.

## Roadmap
- [x] Create a base local API for file and folders.
- [x] Make deployable in a local Docker services.
- [x] Provide and authentication mechanism.
- [ ] Implement a MCP server for the API.
- [ ] Add additional endpoints like DELETE and perhaps MERGE. But I'd want configuration or authorization to be in plact to control access.
- [ ] Provide file/folder metadata. Perhaps integrating file frontmatter into metadata.

