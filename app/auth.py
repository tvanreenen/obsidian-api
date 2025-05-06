from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Optional

security = HTTPBearer()

def get_api_key() -> str:
    """Get the API key from environment variable."""
    api_key = os.getenv("OBSIDIAN_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured. Set OBSIDIAN_API_KEY environment variable."
        )
    return api_key

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify the bearer token against the configured API key."""
    api_key = get_api_key()
    
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True 