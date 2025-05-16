# Running as an MCP Sever

## Current State

- Up and running using FastMCP
- Only set up to run via Streamable HTTP (the replacement for SSE). That said, this is new enough that there isn't much support for this new protocol outside of MCP inspector. See https://www.claudemcp.com/blog/mcp-streamable-http.
- Only works if the auth token is disabled. A static bearer token works for the FastAPI setup, but when run with FastMCP, authentication will fail until OAuth is implemented.
- Works best on a local copy of your Obsidian files (with or without Obsidian Sync); syncing through iCloud has issues that are detailed below.

## What's up With iCloud?

I have traditionally used iCloud to seamlessly sync my Obsidian notes between devices and between the desktop and mobile apps. But while testing the MCP server, I kept getting the intermittent error `[Errno 35] Resource deadlock avoided` when the API accesses the vault via Docker. Apparently iCloud uses background sync and special file attributes, which can interfere with Docker’s file access.

Some possible solutions/workarounds:

- Run the API natively on macOS, accessing the iCloud folder directly.
- Use Obsidian's own sync service.
- Use a sync tool (`rsync`, `Unison`, etc.) to copy changes from the iCloud folder to the local folder.
- Use a tool like Syncthing or Resilio Sync to mirror the iCloud vault to a local folder for the API.

For now, Docker was more important to me than iCloud. And moving to use Obsidian Sync (paid service) was easier than adding another syncing layer. So that's the way I've personally gone for now and it seems to work well.


## What's up With Authentication?

- FastMCP [added support](https://github.com/jlowin/fastmcp/pull/300/files) for OAuth 2.0 authentication. But thier documentation is limited at this point. It supposed to be configured by providing an `auth_server_provider` (a  OAuthAuthorizationServerProvider) and `auth` settings during `FastMCP` initialization.

```python
mcp = FastMCP(
  name="SecureApp",
  auth_server_provider=MyOAuthServerProvider(),
  auth=AuthSettings(
    issuer_url="https://myapp.com",
    # ... other OAuth settings ...
    required_scopes=["myscope"],
  ),
)
```
