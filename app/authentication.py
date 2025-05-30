import os
from fastapi_plugin import Auth0FastAPI

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
API_AUDIENCE = os.getenv("API_AUDIENCE", "")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_SECRET = os.getenv("AUTH0_SECRET", "")

if os.getenv("OBSIDIAN_AUTH_ENABLED", "false").lower() == "true":
    missing = []
    if not AUTH0_DOMAIN:
        missing.append("AUTH0_DOMAIN")
    if not API_AUDIENCE:
        missing.append("API_AUDIENCE")
    if not AUTH0_CLIENT_ID:
        missing.append("AUTH0_CLIENT_ID")
    if not AUTH0_CLIENT_SECRET:
        missing.append("AUTH0_CLIENT_SECRET")
    if not AUTH0_SECRET:
        missing.append("AUTH0_SECRET")
    if missing:
        raise RuntimeError(f"The following required environment variables are not set (but are required when OBSIDIAN_AUTH_ENABLED is true): {', '.join(missing)}")

def get_auth_dependency():
    if os.getenv("OBSIDIAN_AUTH_ENABLED", "false").lower() == "true":
        auth = Auth0FastAPI(domain=AUTH0_DOMAIN, audience=API_AUDIENCE)
        return auth.require_auth()
    else:
        async def allow_all():
            return None
        return allow_all