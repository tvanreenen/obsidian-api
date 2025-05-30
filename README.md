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

---

## Primary File Routes

- `GET /files` - List all markdown files in your vault with their metadata, including path, size, and modification dates
- `GET /files/{path}` - Get the complete file representation including metadata, YAML frontmatter, and markdown body content
- `POST /files/{path}` - Create a new markdown file at the specified path using a JSON object with 'frontmatter' (YAML object) and 'body' (markdown string) fields
- `PUT /files/{path}` - Replace the entire raw content of the file. The content should include YAML frontmatter (between --- markers) followed by markdown body content
- `PATCH /files/{path}` - Merge new metadata with existing file metadata, including moving/renaming the file to a new path within the vault

## Sub-Resource Files Routes

### Raw File

- `GET /files/{path}/raw` - Get the raw contents of the markdown file at the specified path, including frontmatter and body content exactly as stored
- `POST /files/{path}/raw` - Create a new markdown file at the specified path with raw text content. The content should include YAML frontmatter (between --- markers) followed by markdown body content
- `PUT /files/{path}/raw` - Replace the entire raw content of the file. The content should include YAML frontmatter (between --- markers) followed by markdown body content

### File Metadata

- `GET /files/{path}/metadata` - Get the file's metadata including name, path, size, creation date, and last modification date
- `PATCH /files/{path}/metadata` - Merge new metadata with existing file metadata, including moving/renaming the file to a new path within the vault

### Markdown Frontmatter

- `GET /files/{path}/frontmatter` - Get the YAML frontmatter of the file as a JSON object
- `PUT /files/{path}/frontmatter` - Replace the entire YAML frontmatter of the file with a new JSON object containing frontmatter data
- `PATCH /files/{path}/frontmatter` - Merge a new JSON object containing frontmatter data with the existing YAML frontmatter

### Markdown Body

- `GET /files/{path}/body` - Get the markdown body content of the file, excluding the frontmatter section
- `PUT /files/{path}/body` - Replace the entire markdown body content of the file, preserving the frontmatter

## File Response Schema
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

---

## Primary Folder Routes

- `GET /folders` - List all folders in your vault
- `GET /folders/{path}` - Get the folder's metadata including name, path, size, creation date, and last modification date
- `POST /folders/{path}` - Create a new folder at the specified path
- `PATCH /folders/{path}` - Move/rename the folder to a new path within the vault

## Folder Response Schema
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

---

## Setup Your Path

Without authentication enabled, you can simply create a `.env` file in the project root with your Obsidian vault path:
```bash
OBSIDIAN_VAULT_PATH="/path/to/your/obsidian/vault"
```

---

## Setup Authentication

By default, authentication is disabled and no API key is required. To enable authentication, set the following environment variable:

```bash
OBSIDIAN_AUTH_ENABLED=true
```

### Auth0 Setup

Authentication is only supported via Auth0. If you enable authentication by setting `OBSIDIAN_AUTH_ENABLED=true`, you must configure Auth0 as described below.

To use Auth0 for authentication, follow these steps:

1. **Create an API in Auth0:**
   - Go to the [Auth0 Dashboard](https://manage.auth0.com/).
   - Navigate to **APIs** and click **Create API**.
   - Enter a **Name** (e.g., "Obsidian API").
   - Set the **Identifier** (this will be your `API_AUDIENCE`, e.g., `https://your-api.example.com`).
   - Save the API.

2. **Create an Application in Auth0:**
   - Go to **Applications** > **Applications** and click **Create Application**.
   - Enter a **Name** (e.g., "Obsidian API Client").
   - Select **Machine to Machine Applications**.
   - Under **APIs**, authorize your new API (created above).

3. **Configure your `.env` file:**
   - Set the following environment variables in your `.env` file:
     ```bash
     API_AUDIENCE="<your API Identifier from step 1>"
     AUTH0_DOMAIN="<your Auth0 domain, e.g., dev-xxxxxx.us.auth0.com>"
     AUTH0_CLIENT_ID="<your Application's Client ID>"
     AUTH0_CLIENT_SECRET="<your Application's Client Secret>"
     AUTH0_SECRET="<generate a random secret for your app>"
     ```
   - You can generate a secure secret with:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```

### Obtaining and Using an Access Token

After setting up Auth0 as described above, obtain an access token by making a POST request to your Auth0 domain's `/oauth/token` endpoint:

```http
POST https://<AUTH0_DOMAIN>/oauth/token
Content-Type: application/json

{
  "client_id": "<your Auth0 Application's Client ID>",
  "client_secret": "<your Auth0 Application's Client Secret>",
  "audience": "<your API_AUDIENCE>",
  "grant_type": "client_credentials"
}
```

The response will include an `access_token`. For every API request, include the access token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

If the token expires or you receive a 401 Unauthorized error, repeat the `/oauth/token` request to obtain a new access token.

---

## HTTPS Support

> ⚠️ **Warning**: This API does not provide HTTPS natively. To secure your deployment and prevent credentials and sensitive data from being transmitted in plaintext over the internet, you must place it behind a secure reverse proxy (e.g., NGINX, Traefik, or Cloudflare Tunnel) that handles HTTPS.

---

## Testing

Run tests (a few different styles for reference):
```bash
uv run pytest 
uv run pytest tests/test_routes.py
uv run pytest tests/test_routes.py::test_move_file
```
Use the  `-v` flag to provide more detailed output.

---

## Running Locally

```bash
source .env
make serve
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Running via Docker

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

To start the MCP Inspector for testing your MCP server:
```bash
make mcp
```
This will launch the MCP Inspector, allowing you to visually explore and test the MCP server at http://localhost:8001.

---

## Reason for Creating

I've enjoyed using the [Cursor](https://www.cursor.com/)-like [Obsidian Copilot](https://github.com/logancyang/obsidian-copilot) plugin to interact with my knowledge base, but ultimately, I wanted the flexibility to connect it to a wider range of tools—like [N8N](https://n8n.io/), [Claude Desktop](https://claude.ai/download), and various agent- and RAG-based experiments. Building an API was a natural first step toward that and it sounded like an fun hands-on exercise in its own right.

## Roadmap
- [x] Create a base local API for file and folders.
- [x] Make deployable in a local Docker services.
- [x] Provide a basic authentication mechanism.
- [x] File and folder metadata/stats.
- [x] Frontmatter parsing.
- [x] MCP server wrapper around API.
- [x] Provide an OAuth2 Client Credential flow
- [ ] Sync / embedding management for vector store.
- [ ] DELETE methods.

