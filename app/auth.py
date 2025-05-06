from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Initialize with auto_error=False, we'll handle the error in verify_token
security = HTTPBearer(auto_error=False)

def get_server_token() -> str:
    server_token = os.getenv("OBSIDIAN_API_KEY")
    if not server_token:
        raise HTTPException(
            status_code=500,
            detail="API key not configured. Set OBSIDIAN_API_KEY environment variable."
        )
    return server_token

async def verify_token(user_token: HTTPAuthorizationCredentials = Security(security)) -> bool:
    auth_enabled = os.getenv("OBSIDIAN_AUTH_ENABLED", "false").lower() == "true"
    
    if not auth_enabled:
        return True
        
    if not user_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required. Please provide a Bearer token in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    server_token = get_server_token()
    
    if user_token.credentials != server_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Please check your Bearer token and try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True