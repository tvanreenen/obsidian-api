![Obsidian API](obsidian-api.webp)

# Obsidian API

A personal RESTful API (and MCP server) for managing markdown files and folders in your [Obsidian](https://obsidian.md/) vault.

Built with:
- [FastAPI](https://github.com/FastAPI/FastAPI) for the base framework of exposing file operations
- [FastMCP](https://github.com/jlowin/fastmcp) for the option to run as an MCP server instead of an API
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
make serve
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Docker Environment

Build and start the containers:
```bash
make docker-build
make docker-up
```

**This will start two services:**
- The RESTful API on **port 8000**
- The MCP server on **port 8001**

The API will be available at:
- `http://localhost:8000` (from your machine)
- `http://<your-ip-address>:8000` (from other devices on your network)
- `http://obsidian-api:8000` (from other containers in the same Docker network)

The MCP server will be available at:
- `http://localhost:8001` (from your machine)
- `http://<your-ip-address>:8001` (from other devices on your network)
- `http://obsidian-mcp:8001` (from other containers in the same Docker network)

Note: The containers mount your Obsidian vault as a volume at `/mnt/vault` inside the containers.

### How to Connect and Test Locally

To start the RESTful API locally:
```bash
make serve
```
This will launch the API at http://localhost:8000. You can use the included Postman collection in the repo to test the API endpoints interactively.

To start the MCP Inspector for testing your MCP server:
```bash
make mcp
```
This will launch the MCP Inspector, allowing you to visually explore and test the MCP server at http://localhost:8001.

## Security

### Authentication

By default, authentication is disabled and no API key is required. To enable authentication, set the following environment variable:

```bash
OBSIDIAN_AUTH_ENABLED=true
```

You can generate your API key using any secure method, such as `python -c "import secrets; print(secrets.token_urlsafe(32))"`, `openssl rand -hex 32`, or a password manager. Set the generated key using the following environment variable:

```bash
OBSIDIAN_API_KEY=your-secret-api-key
```

Once authentication is enabled, all endpoints will require the generated API key to be passed as a Bearer token in the request header:

```http
Authorization: Bearer your-secret-api-key
```

Notes:

* This is a basic, static, single-token authentication method.
* All clients must use the same key.
* There are no scopes or access limitations.
* Token rotation and revocation are not handled automatically—you must manage them manually.

### HTTPS Support

> ⚠️ **Warning**: This API does not provide HTTPS natively. To secure your deployment and prevent credentials and sensitive data from being transmitted in plaintext over the internet, you must place it behind a secure reverse proxy (e.g., NGINX, Traefik, or Cloudflare Tunnel) that handles HTTPS.

## API

### Files

#### Primary Routes
- `GET /files` - List all markdown files in your vault with their metadata, including path, size, and modification dates
- `GET /files/{path}` - Get the complete file representation including metadata, YAML frontmatter, and markdown body content
- `POST /files/{path}` - Create a new markdown file at the specified path using a JSON object with 'frontmatter' (YAML object) and 'body' (markdown string) fields
- `PUT /files/{path}` - Replace the entire raw content of the file. The content should include YAML frontmatter (between --- markers) followed by markdown body content
- `PATCH /files/{path}` - Merge new metadata with existing file metadata, including moving/renaming the file to a new path within the vault

#### Sub-Resource Routes

##### Raw File

- `GET /files/{path}/raw` - Get the raw contents of the markdown file at the specified path, including frontmatter and body content exactly as stored
- `POST /files/{path}/raw` - Create a new markdown file at the specified path with raw text content. The content should include YAML frontmatter (between --- markers) followed by markdown body content
- `PUT /files/{path}/raw` - Replace the entire raw content of the file. The content should include YAML frontmatter (between --- markers) followed by markdown body content

##### File Metadata

- `GET /files/{path}/metadata` - Get the file's metadata including name, path, size, creation date, and last modification date
- `PATCH /files/{path}/metadata` - Merge new metadata with existing file metadata, including moving/renaming the file to a new path within the vault
##### Markdown Frontmatter

- `GET /files/{path}/frontmatter` - Get the YAML frontmatter of the file as a JSON object
- `PUT /files/{path}/frontmatter` - Replace the entire YAML frontmatter of the file with a new JSON object containing frontmatter data
- `PATCH /files/{path}/frontmatter` - Merge a new JSON object containing frontmatter data with the existing YAML frontmatter
##### Markdown Body

- `GET /files/{path}/body` - Get the markdown body content of the file, excluding the frontmatter section
- `PUT /files/{path}/body` - Replace the entire markdown body content of the file, preserving the frontmatter

#### Response Schema
```json
{
  "metadata": {
    "name": "string",
    "path": "string",
    "type": "file",
    "size": 0,
    "created": "datetime",
    "modified": "datetime"
  },
  "content": {
    "frontmatter": {
      "key": "value"
    },
    "body": "string"
  }
}
```

### Folders

#### Primary Routes

- `GET /folders` - List all folders in your vault
- `GET /folders/{path}` - Get the folder's metadata including name, path, size, creation date, and last modification date
- `POST /folders/{path}` - Create a new folder at the specified path
- `PATCH /folders/{path}` - Move/rename the folder to a new path within the vault

#### Response Schema
```json
{
  "metadata": {
    "name": "string",
    "path": "string",
    "type": "folder",
    "created": "datetime",
    "modified": "datetime"
  }
}
```

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
- [x] Provide an authentication mechanism.
- [x] File and folder metadata/stats.
- [x] Frontmatter parsing.
- [ ] MCP server wrapper around API.
- [ ] Sync / embedding management for vector store.
- [ ] DELETE methods.

