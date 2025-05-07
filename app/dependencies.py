import os
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

class ObsidianHTTPBearer:    
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
    
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        if not os.getenv("OBSIDIAN_AUTH_ENABLED", "false").lower() == "true":
            return None

        if not os.getenv("OBSIDIAN_API_KEY"):
            if self.auto_error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API key not configured. Set OBSIDIAN_API_KEY environment variable.")
            return None

        auth = request.headers.get("Authorization")
        if not auth:
            if self.auto_error:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
            return None

        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong authorization scheme")
            return None

        if not token:
            if self.auto_error:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
            return None

        if token != os.getenv("OBSIDIAN_API_KEY"):
            if self.auto_error:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")
            return None

        return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)